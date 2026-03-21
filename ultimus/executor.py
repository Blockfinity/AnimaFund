"""
Ultimus Executor — Takes prediction strategy and deploys real Anima agents.
Converts simulation personas into genesis prompts.
Hands off to the platform's provisioning system.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
LLM_URL = "https://integrations.emergentagent.com/llm/v1"


class Executor:
    """Converts prediction results into real Anima deployments."""

    async def generate_genesis_prompts(self, strategy: Dict, goal: str) -> List[Dict]:
        """Generate a genesis prompt for each agent role in the strategy."""
        from camel.agents import ChatAgent
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4o-mini",
            api_key=LLM_KEY,
            url=LLM_URL,
        )

        agents_to_deploy = strategy.get("recommended_agents", [])
        genesis_prompts = []

        for agent_spec in agents_to_deploy:
            prompt = f"""Generate a genesis prompt for an autonomous AI agent.

Overall goal: {goal}
This agent's role: {agent_spec.get('role', 'General')}
Focus area: {agent_spec.get('genesis_prompt_focus', 'Execute the goal')}
Priority: {agent_spec.get('priority', 'medium')}
Key actions from simulation: {json.dumps(strategy.get('key_actions', [])[:3])}
Risks identified: {json.dumps(strategy.get('risks', [])[:3])}

The genesis prompt must:
1. Define the agent's identity and mission clearly
2. List specific actions to take immediately on boot
3. Include survival economics (check balance, manage burn rate)
4. Include Telegram reporting instructions
5. Be self-contained — the agent operates with NO human guidance after boot

Write the complete genesis prompt (500-1000 words). Start with "You are..."."""

            agent = ChatAgent(system_message="You write genesis prompts for autonomous AI agents.", model=model)
            response = agent.step(prompt)
            content = response.msgs[0].content if response.msgs else ""

            genesis_prompts.append({
                "role": agent_spec.get("role", "General"),
                "priority": agent_spec.get("priority", "medium"),
                "genesis_prompt": content,
                "estimated_cost": agent_spec.get("estimated_cost", 0),
            })

        return genesis_prompts

    async def execute(self, prediction_id: str, strategy: Dict, goal: str,
                      cost_model: Dict, db=None) -> Dict:
        """Execute a prediction — generate prompts and create agent records for deployment."""
        genesis_prompts = await self.generate_genesis_prompts(strategy, goal)

        deployed = []
        waves = cost_model.get("deployment_waves", [{"wave": 1, "agents": []}])
        wave_1_roles = set(waves[0].get("agents", [])) if waves else set()

        for gp in genesis_prompts:
            agent_id = f"anima-{gp['role'].lower().replace(' ', '-')}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
            agent_record = {
                "agent_id": agent_id,
                "name": gp["role"],
                "genesis_prompt": gp["genesis_prompt"],
                "prediction_id": prediction_id,
                "status": "ready_to_deploy" if gp["role"] in wave_1_roles else "queued",
                "wave": 1 if gp["role"] in wave_1_roles else 2,
                "priority": gp["priority"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Save to MongoDB if available
            if db is not None:
                await db.agents.insert_one(agent_record)
                del agent_record["_id"]

            deployed.append(agent_record)
            logger.info(f"Agent created: {agent_id} (role: {gp['role']}, wave: {agent_record['wave']})")

        return {
            "prediction_id": prediction_id,
            "agents_created": len(deployed),
            "agents": deployed,
            "wave_1_count": len(wave_1_roles),
            "total_waves": len(waves),
        }
