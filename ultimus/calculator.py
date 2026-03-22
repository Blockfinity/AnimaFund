"""
Ultimus Calculator — Analyzes goal complexity BEFORE simulation runs.
Determines: persona count, rounds, LLM cost, execution cost, seed capital, break-even.
"""
import os
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Cost per LLM call (approximate)
COST_PER_CALL = {
    "claude-sonnet-4-20250514": 0.003,
    "gpt-4o-mini": 0.0005,
    "gpt-5-mini": 0.001,
    "ultima-x": 0.0,
}

# Cost per agent-hour for execution
COST_PER_AGENT_HOUR = {
    "subprocess": 0.0,      # Free on platform server (development)
    "fly_hobby": 0.05,
    "fly_pro": 0.15,
    "conway_hobby": 0.05,
    "docker": 0.02,
}


async def estimate_prediction(goal: str, mode: str = "quick") -> Dict:
    """Analyze goal and estimate simulation parameters + costs."""
    key = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return _default_estimate(goal, mode)

    from anima_machina.agents import ChatAgent
    from anima_machina.models import ModelFactory
    from anima_machina.types import ModelPlatformType

    try:
        model = ModelFactory.create(model_platform=ModelPlatformType.OPENAI, model_type="gpt-4o-mini",
            api_key=os.environ.get("EMERGENT_LLM_KEY", key), url="https://integrations.emergentagent.com/llm/v1")
    except Exception:
        return _default_estimate(goal, mode)

    agent = ChatAgent(system_message="Analyze prediction goals. Return JSON only.", model=model)
    response = agent.step(f"""Analyze this prediction goal and estimate simulation parameters:

Goal: "{goal}"
Mode: {mode}

Return JSON:
{{
  "complexity": "simple/moderate/complex/extreme",
  "recommended_personas": <number 5-200>,
  "recommended_rounds": <number 3-20>,
  "persona_types": ["type1", "type2", ...],
  "estimated_simulation_minutes": <number>,
  "reasoning": "why these numbers"
}}
ONLY valid JSON.""")

    content = response.msgs[0].content if response.msgs else "{}"
    try:
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        analysis = json.loads(content.strip())
    except json.JSONDecodeError:
        return _default_estimate(goal, mode)

    personas = analysis.get("recommended_personas", 10)
    rounds = analysis.get("recommended_rounds", 5)
    model_name = "claude-sonnet-4-20250514" if os.environ.get("ANTHROPIC_API_KEY") else "gpt-4o-mini"
    cost_per_call = COST_PER_CALL.get(model_name, 0.001)

    # Simulation cost = (persona_generation calls + personas * rounds + strategy analysis)
    sim_calls = 1 + (personas * rounds) + 1
    sim_cost = sim_calls * cost_per_call

    # Execution cost (if user deploys)
    exec_agents = min(personas, 10)  # Cap deployed agents
    exec_cost_per_hour = exec_agents * COST_PER_AGENT_HOUR.get("subprocess", 0)

    return {
        "goal": goal,
        "mode": mode,
        "complexity": analysis.get("complexity", "moderate"),
        "recommended_personas": personas,
        "recommended_rounds": rounds,
        "persona_types": analysis.get("persona_types", []),
        "simulation": {
            "llm_calls": sim_calls,
            "estimated_cost": round(sim_cost, 4),
            "estimated_minutes": analysis.get("estimated_simulation_minutes", personas * rounds * 0.05),
            "model": model_name,
        },
        "execution": {
            "agents_to_deploy": exec_agents,
            "cost_per_hour": round(exec_cost_per_hour, 4),
            "infrastructure": "platform_subprocess",
        },
        "reasoning": analysis.get("reasoning", ""),
    }


def _default_estimate(goal: str, mode: str) -> Dict:
    words = len(goal.split())
    complexity = "simple" if words < 10 else "moderate" if words < 30 else "complex"
    personas = {"simple": 5, "moderate": 10, "complex": 20}.get(complexity, 10)
    rounds = {"simple": 3, "moderate": 5, "complex": 8}.get(complexity, 5)
    return {
        "goal": goal, "mode": mode, "complexity": complexity,
        "recommended_personas": personas, "recommended_rounds": rounds,
        "persona_types": [],
        "simulation": {"llm_calls": 1 + personas * rounds + 1, "estimated_cost": 0, "estimated_minutes": personas * rounds * 0.05, "model": "unknown"},
        "execution": {"agents_to_deploy": min(personas, 10), "cost_per_hour": 0, "infrastructure": "platform_subprocess"},
        "reasoning": "Default estimate based on goal length",
    }
