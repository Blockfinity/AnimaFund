"""
Ultimus Calculator — Computes infrastructure costs, timeline, and feasibility.
Takes prediction output and produces deployment economics.
Does NOT reject predictions — adapts to resource constraints.
"""
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Cost estimates per agent per hour (in USD)
COST_PER_AGENT_HOUR = {
    "conway_hobby": 0.05,   # Conway hobby tier
    "conway_pro": 0.15,     # Conway pro tier
    "generic_small": 0.03,  # Generic small VM
    "generic_medium": 0.10, # Generic medium VM
    "self_hosted": 0.01,    # Self-hosted (power + maintenance)
}

INFERENCE_COST_PER_1K_TOKENS = {
    "gpt-5-mini": 0.001,
    "gpt-4o-mini": 0.0015,
    "ultima-x": 0.0,  # Self-hosted, zero marginal cost
}


class Calculator:
    """Computes deployment costs, timeline, and feasibility from prediction strategy."""

    def calculate(self, strategy: Dict, seed_capital: float = 10.0,
                  provider: str = "conway_hobby", model: str = "gpt-5-mini") -> Dict:
        """Calculate deployment economics from a prediction strategy."""
        agents = strategy.get("recommended_agents", [])
        if not agents:
            return {"error": "No agents in strategy", "feasible": False}

        num_agents = len(agents)
        infra_cost_per_hour = COST_PER_AGENT_HOUR.get(provider, 0.05) * num_agents
        inference_cost_per_hour = INFERENCE_COST_PER_1K_TOKENS.get(model, 0.001) * 50 * num_agents  # ~50K tokens/agent/hour

        total_cost_per_hour = infra_cost_per_hour + inference_cost_per_hour
        hours_funded = seed_capital / total_cost_per_hour if total_cost_per_hour > 0 else float('inf')

        # Calculate break-even based on strategy's estimated revenue
        estimated_revenue_per_hour = strategy.get("total_seed_cost", 0) / max(strategy.get("estimated_break_even_hours", 1), 1)

        break_even_hours = None
        if estimated_revenue_per_hour > total_cost_per_hour:
            break_even_hours = seed_capital / (estimated_revenue_per_hour - total_cost_per_hour)

        # Per-agent breakdown
        agent_costs = []
        for agent_spec in agents:
            agent_cost = {
                "role": agent_spec.get("role", "unknown"),
                "priority": agent_spec.get("priority", "medium"),
                "infra_per_hour": COST_PER_AGENT_HOUR.get(provider, 0.05),
                "inference_per_hour": INFERENCE_COST_PER_1K_TOKENS.get(model, 0.001) * 50,
                "estimated_one_time": agent_spec.get("estimated_cost", 0),
            }
            agent_cost["total_per_hour"] = agent_cost["infra_per_hour"] + agent_cost["inference_per_hour"]
            agent_costs.append(agent_cost)

        # Deployment waves (if can't afford all at once)
        waves = self._plan_waves(agents, seed_capital, COST_PER_AGENT_HOUR.get(provider, 0.05))

        return {
            "feasible": True,
            "num_agents": num_agents,
            "seed_capital": seed_capital,
            "total_cost_per_hour": round(total_cost_per_hour, 4),
            "hours_funded": round(hours_funded, 1),
            "break_even_hours": round(break_even_hours, 1) if break_even_hours else None,
            "self_sustaining": break_even_hours is not None and break_even_hours < hours_funded,
            "agent_costs": agent_costs,
            "deployment_waves": waves,
            "provider": provider,
            "model": model,
            "confidence": strategy.get("confidence_score", 0.5),
        }

    def _plan_waves(self, agents: List[Dict], capital: float, cost_per_agent: float) -> List[Dict]:
        """Plan deployment waves based on available capital."""
        if not agents:
            return []

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_agents = sorted(agents, key=lambda a: priority_order.get(a.get("priority", "medium"), 1))

        waves = []
        remaining_capital = capital
        wave_agents = []
        wave_num = 1

        for agent in sorted_agents:
            agent_startup_cost = agent.get("estimated_cost", 0) + cost_per_agent * 24  # 24 hours runway
            if remaining_capital >= agent_startup_cost:
                wave_agents.append(agent.get("role", "unknown"))
                remaining_capital -= agent_startup_cost
            else:
                if wave_agents:
                    waves.append({"wave": wave_num, "agents": wave_agents, "capital_needed": capital - remaining_capital})
                    wave_num += 1
                    wave_agents = [agent.get("role", "unknown")]
                    remaining_capital = 0  # Future waves funded by revenue
                else:
                    wave_agents.append(agent.get("role", "unknown"))

        if wave_agents:
            waves.append({"wave": wave_num, "agents": wave_agents,
                         "capital_needed": sum(a.get("estimated_cost", 0) for a in sorted_agents) if wave_num > 1 else capital - remaining_capital})

        return waves
