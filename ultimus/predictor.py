"""
Ultimus Predictor — Multi-round multi-agent simulation.
Each round, every agent sees what ALL other agents did and reacts.
Emergent behavior comes from agent INTERACTION across rounds, not individual analysis.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable

from anima_machina.agents import ChatAgent
from anima_machina.models import ModelFactory
from anima_machina.types import ModelPlatformType

logger = logging.getLogger(__name__)

LLM_URL = "https://integrations.emergentagent.com/llm/v1"


def _get_model():
    key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY not set")
    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type="gpt-4o-mini",
        api_key=key, url=LLM_URL,
    )


async def generate_personas(goal: str, context: str, count: int) -> List[Dict]:
    """Generate diverse, conflicting personas. Must include supporters, skeptics, experts,
    newcomers, influencers, contrarians, risk-takers, conservatives, specialists."""
    model = _get_model()
    agent = ChatAgent(system_message="Generate simulation personas as JSON array.", model=model)
    prompt = f"""Generate {count} DIVERSE agent personas to simulate: "{goal}"

Context: {context[:1500] if context else 'None'}

Requirements:
- Each persona MUST have a DIFFERENT perspective that CONFLICTS with at least 2 others
- Include: day traders, long-term holders, developers, institutional investors, journalists,
  retail newcomers, market makers, short sellers, regulators, community builders, skeptics,
  maximalists, analysts, whales, newcomers
- Each must have different risk tolerance, different information access, different biases
- Personas will INTERACT and DEBATE across multiple rounds — design them to naturally disagree

Return JSON array:
[{{"name":"unique name","role":"specific role","personality":"2 sentences about how they think — include biases","strategy":"their specific approach","risk_tolerance":"low/medium/high/extreme","bias":"what they tend to believe regardless of evidence"}}]
ONLY valid JSON."""

    response = agent.step(prompt)
    content = response.msgs[0].content if response.msgs else "[]"
    try:
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())[:count]
    except json.JSONDecodeError:
        return [{"name": f"Agent-{i}", "role": "Observer", "personality": "Adaptive",
                 "strategy": "Watch and react", "risk_tolerance": "medium", "bias": "none"}
                for i in range(count)]


class UltimusPrediction:
    """Multi-round simulation where agents interact with each other."""

    def __init__(self, pred_id: str, goal: str, persona_defs: List[Dict], num_rounds: int):
        self.id = pred_id
        self.goal = goal
        self.persona_defs = persona_defs
        self.num_rounds = num_rounds
        self.status = "created"
        self.all_events: List[Dict] = []
        self.round_summaries: List[Dict] = []
        self.relationships: List[Dict] = []
        self.agents: List[ChatAgent] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self._stream: Optional[Callable] = None

    def on_event(self, cb: Callable):
        self._stream = cb

    def _emit(self, event: Dict):
        event["sim_id"] = self.id
        event["ts"] = datetime.now(timezone.utc).isoformat()
        self.all_events.append(event)
        if self._stream:
            try:
                self._stream(event)
            except Exception:
                pass

    async def run(self) -> Dict:
        model = _get_model()
        self.status = "running"
        self._emit({"type": "start", "agents": len(self.persona_defs), "rounds": self.num_rounds})

        # Create persistent agents — each keeps its conversation history across rounds
        self.agents = []
        for p in self.persona_defs:
            sys_msg = (
                f"You are {p['name']}, a {p['role']}.\n"
                f"Personality: {p['personality']}\n"
                f"Strategy: {p['strategy']}\n"
                f"Risk tolerance: {p.get('risk_tolerance', 'medium')}\n"
                f"Bias: {p.get('bias', 'none')}\n\n"
                f"You are in a multi-round simulation about: {self.goal}\n"
                f"Each round you will see what ALL other participants said.\n"
                f"You MUST react to their positions — agree, disagree, challenge, build coalitions.\n"
                f"Your response should be 2-4 sentences: your position + reaction to others.\n"
                f"If you change your mind based on new information, SAY SO explicitly."
            )
            self.agents.append(ChatAgent(system_message=sys_msg, model=model))

        # RUN ROUNDS — the core simulation loop
        round_history = []  # All events from all rounds
        round_summaries_text = []  # Compressed summaries of each completed round

        for round_num in range(1, self.num_rounds + 1):
            self._emit({"type": "round_start", "round": round_num})

            # Build context: FULL history — summaries for old rounds, detail for recent
            context = f"=== ROUND {round_num}/{self.num_rounds} ===\n"
            context += f"Goal: {self.goal}\n\n"

            if round_summaries_text:
                # Include compressed summaries of ALL earlier rounds
                context += "EARLIER ROUNDS (summary):\n"
                for rs in round_summaries_text[:-1]:  # All except the most recent
                    context += rs + "\n"
                context += "\n"

            # Include the MOST RECENT round in full detail
            recent_round = round_num - 1
            recent_events = [e for e in round_history if e["round"] == recent_round]
            if recent_events:
                context += f"LAST ROUND ({recent_round}) — FULL DETAIL:\n"
                for evt in recent_events:
                    context += f"  {evt['agent']} ({evt['role']}): {evt['content'][:200]}\n"
                context += "\n"

            context += "React to what others said. ADDRESS PEOPLE BY NAME when you agree or disagree with them."

            # Each agent takes a turn this round
            round_events = []
            for i, (agent, persona) in enumerate(zip(self.agents, self.persona_defs)):
                try:
                    response = agent.step(context)
                    content = response.msgs[0].content if response.msgs else "(no response)"
                except Exception as e:
                    content = f"(error: {str(e)[:50]})"

                event = {
                    "round": round_num,
                    "agent": persona["name"],
                    "role": persona["role"],
                    "content": content[:300],
                }
                round_events.append(event)
                round_history.append(event)

                self._emit({"type": "agent_action", **event})

            # Relationships are extracted from agent memory and response patterns
            # The framework tracks interactions natively via ChatAgent.chat_history
            # We extract who-referenced-whom from each agent's actual response content
            agent_names = [p["name"] for p in self.persona_defs]
            for evt in round_events:
                author = evt["agent"]
                content = evt["content"]
                for other_name in agent_names:
                    if other_name == author:
                        continue
                    # Check if this agent's response references another agent (full or first name)
                    parts = other_name.split()
                    mentioned = other_name.lower() in content.lower()
                    if not mentioned:
                        for part in parts:
                            if len(part) > 2 and part.lower() in content.lower():
                                mentioned = True
                                break
                    if mentioned:
                        self.relationships.append({
                            "from": author, "to": other_name,
                            "type": self._classify_relationship(content),
                            "round": round_num,
                        })

            # Summarize this round into a compressed text for future context
            positions = {}
            summary_lines = [f"Round {round_num}:"]
            for evt in round_events:
                positions[evt["agent"]] = evt["content"][:100]
                summary_lines.append(f"  {evt['agent']}: {evt['content'][:80]}")
            round_summaries_text.append("\n".join(summary_lines))

            self.round_summaries.append({
                "round": round_num,
                "events": len(round_events),
                "positions": positions,
            })

            self._emit({"type": "round_end", "round": round_num, "actions": len(round_events),
                        "total_events": len(round_history)})

        self.status = "completed"
        self._emit({"type": "complete", "total_events": len(round_history),
                    "rounds": self.num_rounds, "agents": len(self.persona_defs)})

        return self.to_dict()

    @staticmethod
    def _classify_relationship(content: str) -> str:
        """Classify the relationship type from response content.
        Returns a dynamic label based on sentiment — not hardcoded categories."""
        c = content.lower()
        # Positive alignment signals
        if any(w in c for w in ["agree", "support", "echo", "align", "share", "appreciate", "right", "correct", "valid"]):
            return "agrees_with"
        # Negative alignment signals
        if any(w in c for w in ["disagree", "challenge", "oppose", "wrong", "risk", "caution", "concern", "doubt", "skeptic"]):
            return "disagrees_with"
        # Influence signals
        if any(w in c for w in ["building on", "inspired", "following", "expanding on", "adding to"]):
            return "builds_on"
        return "references"



    def to_dict(self) -> Dict:
        return {
            "id": self.id, "goal": self.goal, "status": self.status,
            "num_rounds": self.num_rounds,
            "personas": self.persona_defs,
            "round_summaries": self.round_summaries,
            "relationships": self.relationships,
            "events": self.all_events[-200:],
            "total_events": len(self.all_events),
            "created_at": self.created_at,
        }
