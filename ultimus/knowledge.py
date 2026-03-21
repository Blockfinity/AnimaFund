"""
Ultimus Knowledge Graph — Extracts entities and relationships from seed data.
Uses LLM to parse text into a knowledge graph. No Neo4j dependency — stores in MongoDB.
Feeds into the Predictor for Deep/Expert/Iterative prediction modes.
"""
import os
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

LLM_URL = "https://integrations.emergentagent.com/llm/v1"


class KnowledgeGraph:
    """Lightweight knowledge graph — entities + relationships stored as dicts."""

    def __init__(self):
        self.entities: List[Dict] = []
        self.relationships: List[Dict] = []

    def to_dict(self) -> dict:
        return {"entities": self.entities, "relationships": self.relationships,
                "entity_count": len(self.entities), "relationship_count": len(self.relationships)}

    def get_context_for_simulation(self) -> str:
        """Produce a text summary the Predictor can use as seed data."""
        parts = []
        if self.entities:
            parts.append("Key entities: " + ", ".join(
                f"{e['name']} ({e['type']})" for e in self.entities[:20]))
        if self.relationships:
            parts.append("Key relationships: " + "; ".join(
                f"{r['from']} --[{r['type']}]--> {r['to']}" for r in self.relationships[:20]))
        return "\n".join(parts)


async def build_knowledge_graph(text: str, goal: str = "") -> KnowledgeGraph:
    """Extract entities and relationships from text using LLM."""
    llm_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not llm_key:
        logger.warning("No LLM key — returning empty knowledge graph")
        return KnowledgeGraph()

    from anima_machina.agents import ChatAgent
    from anima_machina.models import ModelFactory
    from anima_machina.types import ModelPlatformType

    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type="gpt-4o-mini",
        api_key=llm_key,
        url=LLM_URL,
    )

    prompt = f"""Extract entities and relationships from this text. Context goal: "{goal}"

TEXT:
{text[:3000]}

Return JSON with exactly this format:
{{
  "entities": [
    {{"name": "Entity Name", "type": "Person|Organization|Technology|Market|Strategy|Risk|Platform", "description": "brief description"}}
  ],
  "relationships": [
    {{"from": "Entity A", "to": "Entity B", "type": "uses|competes_with|funds|regulates|depends_on|creates|trades_on|provides", "description": "brief description"}}
  ]
}}
Return ONLY valid JSON."""

    agent = ChatAgent(system_message="You extract knowledge graphs from text. Return only JSON.", model=model)
    response = agent.step(prompt)
    content = response.msgs[0].content if response.msgs else "{}"

    try:
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content.strip())
    except json.JSONDecodeError:
        logger.warning("Failed to parse knowledge graph JSON")
        data = {"entities": [], "relationships": []}

    kg = KnowledgeGraph()
    kg.entities = data.get("entities", [])[:50]
    kg.relationships = data.get("relationships", [])[:100]
    return kg


async def build_from_web_search(goal: str) -> KnowledgeGraph:
    """Deep Predict mode — auto-research via web search, build knowledge graph."""
    llm_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not llm_key:
        return KnowledgeGraph()

    from anima_machina.agents import ChatAgent
    from anima_machina.models import ModelFactory
    from anima_machina.types import ModelPlatformType

    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type="gpt-4o-mini",
        api_key=llm_key,
        url=LLM_URL,
    )

    # Step 1: Generate research context from the goal
    research_agent = ChatAgent(
        system_message="You are a research analyst. Given a goal, produce a comprehensive domain analysis covering key players, technologies, strategies, risks, and market dynamics. Be specific and data-rich.",
        model=model,
    )
    research = research_agent.step(f"Research this domain thoroughly for prediction purposes: {goal}")
    research_text = research.msgs[0].content if research.msgs else ""

    # Step 2: Extract knowledge graph from research
    return await build_knowledge_graph(research_text, goal)
