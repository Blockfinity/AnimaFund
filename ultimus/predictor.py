"""
Ultimus Predictor — Uses Anima Machina's Workforce for real multi-agent simulation.
NOT a custom simulation engine. Uses Anima Machina's built-in orchestration.
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable

from anima_machina.societies.workforce import Workforce
from anima_machina.agents import ChatAgent
from anima_machina.models import ModelFactory
from anima_machina.types import ModelPlatformType
from anima_machina.toolkits import FunctionTool

logger = logging.getLogger(__name__)

LLM_URL = "https://integrations.emergentagent.com/llm/v1"


def _get_model():
    key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not key:
        raise RuntimeError("EMERGENT_LLM_KEY not set")
    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type="gpt-4o-mini",
        api_key=key,
        url=LLM_URL,
    )


async def generate_personas(goal: str, context: str, count: int) -> List[Dict]:
    """Generate diverse persona definitions from goal + knowledge context."""
    model = _get_model()
    agent = ChatAgent(
        system_message="Generate simulation personas as a JSON array. Each must be unique.",
        model=model,
    )
    prompt = f"""Generate {count} diverse personas to simulate: "{goal}"

Context: {context[:2000] if context else 'No additional context.'}

Each persona needs a distinct perspective — include supporters, skeptics, experts, newcomers, influencers, contrarians, risk-takers, conservatives.

Return JSON array:
[{{"name":"...","role":"...","personality":"2 sentences","strategy":"specific approach","risk_tolerance":"low/medium/high"}}]
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
                 "strategy": "Observe and react", "risk_tolerance": "medium"} for i in range(count)]


class UltimusPrediction:
    """A prediction run using Workforce for multi-agent orchestration."""

    def __init__(self, pred_id: str, goal: str, persona_defs: List[Dict], num_rounds: int):
        self.id = pred_id
        self.goal = goal
        self.persona_defs = persona_defs
        self.num_rounds = num_rounds
        self.status = "created"
        self.events: List[Dict] = []
        self.result: Optional[Dict] = None
        self.workforce: Optional[Workforce] = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self._event_callback: Optional[Callable] = None

    def on_event(self, cb: Callable):
        self._event_callback = cb

    def _emit(self, event: Dict):
        event["sim_id"] = self.id
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.events.append(event)
        if self._event_callback:
            try:
                self._event_callback(event)
            except Exception:
                pass

    async def run(self) -> Dict:
        """Run the prediction using Workforce orchestration."""
        model = _get_model()
        self.status = "running"
        self._emit({"type": "start", "personas": len(self.persona_defs), "rounds": self.num_rounds})

        # Build the task description that the Workforce will decompose and execute
        persona_descriptions = "\n".join(
            f"- {p['name']} ({p['role']}): {p['personality']} Strategy: {p['strategy']} Risk: {p.get('risk_tolerance','medium')}"
            for p in self.persona_defs
        )

        task_description = f"""PREDICTION SIMULATION

Goal to predict: {self.goal}

You are running a multi-round prediction simulation with {len(self.persona_defs)} personas.
Each round, every persona must analyze the current situation and take an action (share analysis, propose strategy, challenge others, form alliances, or change position).

Personas:
{persona_descriptions}

Run {self.num_rounds} rounds of simulation. In each round:
1. Present the current state to all personas
2. Each persona decides their action based on their personality, strategy, and what others did
3. Record all actions and how the group dynamics evolve
4. Identify emerging patterns, coalitions, and strategies

After all rounds, produce a PREDICTION REPORT with:
- Winning strategies (which approaches worked)
- Failed strategies (which didn't)
- Emergent behaviors (what the group did that no individual planned)
- Recommended real-world actions
- Confidence level (0-1)
- Risk assessment

This is NOT a debate. It's a simulation where each persona acts independently based on their own logic."""

        # Create Workforce with stream callback
        self.workforce = Workforce(
            description=f"Ultimus prediction: {self.goal}",
            default_model=model,
            stream_callback=lambda msg: self._emit({"type": "workforce_event", "message": str(msg)[:200]}),
        )

        # Add each persona as a worker
        for persona_def in self.persona_defs:
            system_msg = (
                f"You are {persona_def['name']}, a {persona_def['role']}.\n"
                f"Personality: {persona_def['personality']}\n"
                f"Strategy: {persona_def['strategy']}\n"
                f"Risk tolerance: {persona_def.get('risk_tolerance', 'medium')}\n\n"
                f"In this simulation, you must act according to your personality and strategy. "
                f"When asked to take an action, respond with what you would actually do — "
                f"not what's theoretically optimal. Stay in character."
            )
            worker_agent = ChatAgent(system_message=system_msg, model=model)
            self.workforce.add_single_agent_worker(
                description=f"{persona_def['name']} — {persona_def['role']}: {persona_def['personality'][:50]}",
                worker=worker_agent,
            )

        self._emit({"type": "workers_added", "count": len(self.persona_defs)})

        # Process the prediction task
        try:
            from anima_machina.tasks import Task
            task = Task(
                content=task_description,
                id=self.id,
            )
            self._emit({"type": "simulation_starting"})
            result = await self.workforce.process_task_async(task)

            self.result = {
                "task_result": str(result.result) if hasattr(result, 'result') else str(result),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            self.status = "completed"
            self._emit({"type": "simulation_complete", "result_length": len(str(result))})

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            self.status = "failed"
            self.result = {"error": str(e)}
            self._emit({"type": "error", "error": str(e)})

        return self.to_dict()

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "goal": self.goal, "status": self.status,
            "num_rounds": self.num_rounds,
            "personas": self.persona_defs,
            "events": self.events[-100:],
            "result": self.result,
            "created_at": self.created_at,
        }
