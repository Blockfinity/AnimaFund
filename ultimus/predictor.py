"""
Ultimus Predictor — Simulates scenarios with multiple AI personas.
Uses Anima Machina (CAMEL) multi-agent societies to run non-linear simulations.
Each persona has: personality, strategy, risk tolerance, action capabilities.
Explores thousands of paths simultaneously.
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
LLM_URL = "https://integrations.emergentagent.com/llm/v1"


class Persona:
    """A simulated agent persona with personality, strategy, and capabilities."""

    def __init__(self, name: str, role: str, personality: str, strategy: str, tools: List[str]):
        self.name = name
        self.role = role
        self.personality = personality
        self.strategy = strategy
        self.tools = tools
        self.actions: List[Dict] = []
        self.revenue = 0.0
        self.expenses = 0.0
        self.relationships: Dict[str, str] = {}

    def to_dict(self) -> dict:
        return {
            "name": self.name, "role": self.role,
            "personality": self.personality, "strategy": self.strategy,
            "tools": self.tools, "actions_count": len(self.actions),
            "revenue": self.revenue, "expenses": self.expenses,
        }


class SimulationRound:
    """One round of simulation where all personas act."""

    def __init__(self, round_num: int, personas: List[Persona]):
        self.round_num = round_num
        self.personas = personas
        self.events: List[Dict] = []
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "round": self.round_num,
            "events": self.events,
            "timestamp": self.timestamp,
        }


class Prediction:
    """A complete prediction run with its personas, rounds, and results."""

    def __init__(self, prediction_id: str, goal: str, mode: str):
        self.id = prediction_id
        self.goal = goal
        self.mode = mode  # quick, deep, expert, iterative
        self.status = "created"
        self.personas: List[Persona] = []
        self.rounds: List[SimulationRound] = []
        self.strategy: Optional[Dict] = None
        self.cost_model: Optional[Dict] = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.completed_at: Optional[str] = None
        self.progress = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "goal": self.goal, "mode": self.mode,
            "status": self.status, "progress": self.progress,
            "personas": [p.to_dict() for p in self.personas],
            "rounds_completed": len(self.rounds),
            "strategy": self.strategy, "cost_model": self.cost_model,
            "created_at": self.created_at, "completed_at": self.completed_at,
        }


class Predictor:
    """Runs multi-persona simulations using LLM-powered agents."""

    def __init__(self):
        self._predictions: Dict[str, Prediction] = {}

    async def create_prediction(self, goal: str, mode: str = "quick",
                                num_personas: int = 5, num_rounds: int = 3,
                                seed_data: str = "") -> Prediction:
        """Create and start a new prediction simulation."""
        pred_id = f"pred-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        pred = Prediction(pred_id, goal, mode)
        self._predictions[pred_id] = pred

        # Step 1: Generate personas based on the goal
        pred.status = "generating_personas"
        pred.progress = 0.1
        pred.personas = await self._generate_personas(goal, mode, num_personas, seed_data)
        pred.progress = 0.3

        # Step 2: Run simulation rounds
        pred.status = "simulating"
        for round_num in range(1, num_rounds + 1):
            sim_round = await self._run_round(pred, round_num)
            pred.rounds.append(sim_round)
            pred.progress = 0.3 + (0.4 * round_num / num_rounds)

        # Step 3: Generate strategy from simulation results
        pred.status = "analyzing"
        pred.progress = 0.8
        pred.strategy = await self._generate_strategy(pred)

        pred.status = "completed"
        pred.progress = 1.0
        pred.completed_at = datetime.now(timezone.utc).isoformat()

        return pred

    async def _generate_personas(self, goal: str, mode: str,
                                  num_personas: int, seed_data: str) -> List[Persona]:
        """Use LLM to generate diverse agent personas for the simulation."""
        from camel.agents import ChatAgent
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4o-mini",
            api_key=LLM_KEY,
            url=LLM_URL,
        )

        prompt = f"""Generate {num_personas} diverse agent personas for this goal: "{goal}"

Each persona must have:
- name: unique agent name
- role: specific function (e.g., "DeFi Trader", "Content Creator", "Infrastructure Manager")
- personality: behavioral traits that affect decision-making
- strategy: specific approach to contributing to the goal
- tools: list of 3-5 tools they would use (from: browser, terminal, code_execution, wallet, social_media, web_search, file_ops, api_calls)

{"Seed data context: " + seed_data[:500] if seed_data else "No seed data — generate based on goal alone."}

Return as JSON array: [{{"name": "...", "role": "...", "personality": "...", "strategy": "...", "tools": ["..."]}}]
Return ONLY valid JSON, no other text."""

        agent = ChatAgent(system_message="You generate agent personas as JSON arrays.", model=model)
        response = agent.step(prompt)
        content = response.msgs[0].content if response.msgs else "[]"

        # Parse JSON from response
        try:
            # Handle markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            personas_data = json.loads(content.strip())
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse personas JSON, creating defaults")
            personas_data = [
                {"name": f"Agent-{i}", "role": "General", "personality": "Adaptive",
                 "strategy": "Explore and exploit", "tools": ["browser", "terminal", "wallet"]}
                for i in range(num_personas)
            ]

        return [Persona(**p) for p in personas_data[:num_personas]]

    async def _run_round(self, pred: Prediction, round_num: int) -> SimulationRound:
        """Run one simulation round where each persona decides and acts."""
        from camel.agents import ChatAgent
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4o-mini",
            api_key=LLM_KEY,
            url=LLM_URL,
        )

        sim_round = SimulationRound(round_num, pred.personas)
        context = f"Goal: {pred.goal}\nRound: {round_num}\nPrevious rounds: {len(pred.rounds)}"

        if pred.rounds:
            last_events = pred.rounds[-1].events[-5:]
            context += f"\nRecent events: {json.dumps(last_events)}"

        for persona in pred.personas:
            prompt = f"""{context}

You are simulating persona "{persona.name}" (role: {persona.role}).
Personality: {persona.personality}
Strategy: {persona.strategy}
Tools: {', '.join(persona.tools)}
Revenue so far: ${persona.revenue:.2f}, Expenses: ${persona.expenses:.2f}

What action does this persona take in round {round_num}?
Consider: what tools they use, what they interact with, revenue/cost impact.

Return JSON: {{"action": "...", "tool_used": "...", "outcome": "...", "revenue_delta": 0.0, "expense_delta": 0.0, "confidence": 0.8}}
Return ONLY valid JSON."""

            agent = ChatAgent(system_message="You simulate agent personas. Return only JSON.", model=model)
            response = agent.step(prompt)
            content = response.msgs[0].content if response.msgs else "{}"

            try:
                if "```" in content:
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                event = json.loads(content.strip())
            except json.JSONDecodeError:
                event = {"action": "Explored opportunities", "tool_used": "browser",
                         "outcome": "Found potential leads", "revenue_delta": 0, "expense_delta": 0.1, "confidence": 0.5}

            event["persona"] = persona.name
            event["round"] = round_num
            persona.revenue += event.get("revenue_delta", 0)
            persona.expenses += event.get("expense_delta", 0)
            persona.actions.append(event)
            sim_round.events.append(event)

        return sim_round

    async def _generate_strategy(self, pred: Prediction) -> Dict:
        """Analyze simulation results and produce a deployment strategy."""
        from camel.agents import ChatAgent
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4o-mini",
            api_key=LLM_KEY,
            url=LLM_URL,
        )

        # Summarize simulation
        personas_summary = [{"name": p.name, "role": p.role, "revenue": p.revenue,
                            "expenses": p.expenses, "actions": len(p.actions)} for p in pred.personas]
        total_revenue = sum(p.revenue for p in pred.personas)
        total_expenses = sum(p.expenses for p in pred.personas)

        prompt = f"""Analyze this simulation and produce a deployment strategy.

Goal: {pred.goal}
Rounds completed: {len(pred.rounds)}
Personas: {json.dumps(personas_summary)}
Total simulated revenue: ${total_revenue:.2f}
Total simulated expenses: ${total_expenses:.2f}

Return a strategy as JSON:
{{
  "summary": "1-2 sentence strategy summary",
  "recommended_agents": [
    {{"role": "...", "genesis_prompt_focus": "...", "priority": "high/medium/low", "estimated_cost": 0.0}}
  ],
  "total_seed_cost": 0.0,
  "estimated_break_even_hours": 0,
  "confidence_score": 0.0,
  "risks": ["..."],
  "key_actions": ["..."]
}}
Return ONLY valid JSON."""

        agent = ChatAgent(system_message="You analyze simulations. Return only JSON.", model=model)
        response = agent.step(prompt)
        content = response.msgs[0].content if response.msgs else "{}"

        try:
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {"summary": "Strategy generation failed", "confidence_score": 0.0}

    def get_prediction(self, prediction_id: str) -> Optional[Prediction]:
        return self._predictions.get(prediction_id)

    def list_predictions(self) -> List[Dict]:
        return [p.to_dict() for p in self._predictions.values()]
