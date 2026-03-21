"""
Ultimus Executor — Converts simulation results into REAL running agents.
Each simulation persona becomes a ChatAgent process on the platform server.
Reports state to the dashboard via webhook.
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List

logger = logging.getLogger(__name__)


class Executor:
    """Deploys real Anima Machina agents from simulation results."""

    _running_agents: Dict[str, asyncio.Task] = {}

    async def execute(self, prediction_id: str, strategy: Dict, goal: str,
                      cost_model: Dict, db=None) -> Dict:
        """Convert simulation personas into real running agents."""
        recommended = strategy.get("recommended_agents", [])
        if not recommended:
            return {"error": "No agents to deploy", "agents_created": 0}

        # Generate genesis prompts from strategy
        genesis_prompts = await self._generate_prompts(recommended, goal, strategy)

        deployed = []
        for gp in genesis_prompts:
            agent_id = f"anima-{gp['role'].lower().replace(' ', '-').replace('/', '-')[:20]}-{datetime.now(timezone.utc).strftime('%H%M%S')}"

            agent_record = {
                "agent_id": agent_id,
                "name": gp["role"],
                "genesis_prompt": gp["genesis_prompt"],
                "prediction_id": prediction_id,
                "status": "deploying",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            if db is not None:
                await db.agents.update_one({"agent_id": agent_id}, {"$set": agent_record}, upsert=True)

            # Start the agent as a background task on the platform server
            task = asyncio.create_task(self._run_agent(agent_id, gp["genesis_prompt"], gp["role"]))
            self._running_agents[agent_id] = task
            agent_record["status"] = "running"
            deployed.append({"agent_id": agent_id, "name": gp["role"], "status": "running"})
            logger.info(f"Agent deployed: {agent_id}")

        return {
            "prediction_id": prediction_id,
            "agents_created": len(deployed),
            "agents": deployed,
        }

    async def _generate_prompts(self, agents: List[Dict], goal: str, strategy: Dict) -> List[Dict]:
        """Generate genesis prompts for each recommended agent."""
        key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
        if not key:
            return [{"role": a.get("role", "Agent"), "genesis_prompt": f"You are {a.get('role')}. Goal: {goal}. Focus: {a.get('genesis_prompt_focus','Execute')}."} for a in agents]

        from anima_machina.agents import ChatAgent
        from anima_machina.models import ModelFactory
        from anima_machina.types import ModelPlatformType

        if os.environ.get("ANTHROPIC_API_KEY"):
            model = ModelFactory.create(model_platform=ModelPlatformType.ANTHROPIC, model_type="claude-sonnet-4-20250514", model_config_dict={"max_tokens": 1024})
        else:
            model = ModelFactory.create(model_platform=ModelPlatformType.OPENAI, model_type="gpt-4o-mini", api_key=key, url="https://integrations.emergentagent.com/llm/v1")

        results = []
        for agent_spec in agents[:10]:  # Cap at 10 to save credits
            prompt = f"""Write a genesis prompt for an autonomous agent.
Goal: {goal}
Role: {agent_spec.get('role', 'General')}
Focus: {agent_spec.get('genesis_prompt_focus', 'Execute the goal')}
Strategy context: {strategy.get('summary', '')}

The prompt must be self-contained (200-400 words). The agent will operate with NO human input after boot.
Include: identity, immediate actions, tools to use, reporting instructions, success criteria.
Start with "You are..."."""

            gen_agent = ChatAgent(system_message="Write agent genesis prompts.", model=model)
            response = gen_agent.step(prompt)
            content = response.msgs[0].content if response.msgs else f"You are {agent_spec.get('role')}. Goal: {goal}."

            results.append({"role": agent_spec.get("role", "Agent"), "genesis_prompt": content})

        return results

    async def _run_agent(self, agent_id: str, genesis_prompt: str, role: str):
        """Run an agent as a background process on the platform server."""
        import httpx
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "")
        key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")

        def webhook(data):
            data.update(agent_id=agent_id, timestamp=datetime.now(timezone.utc).isoformat())
            try: httpx.post(f"{api_url}/api/webhook/agent-update", json=data, headers={"Content-Type": "application/json"}, timeout=5)
            except: pass

        webhook({"type": "state", "status": "running", "message": f"{role} agent started", "engine_running": True})

        try:
            from anima_machina.agents import ChatAgent
            from anima_machina.models import ModelFactory
            from anima_machina.types import ModelPlatformType
            from anima_machina.toolkits import TerminalToolkit, CodeExecutionToolkit, SearchToolkit, FunctionTool

            if os.environ.get("ANTHROPIC_API_KEY"):
                model = ModelFactory.create(model_platform=ModelPlatformType.ANTHROPIC, model_type="claude-sonnet-4-20250514", model_config_dict={"max_tokens": 1024})
            else:
                model = ModelFactory.create(model_platform=ModelPlatformType.OPENAI, model_type="gpt-4o-mini", api_key=key, url="https://integrations.emergentagent.com/llm/v1")

            def report(action: str, tool_name: str = "") -> str:
                webhook({"type": "action", "action": action, "tool_name": tool_name})
                return json.dumps({"reported": True})

            tools = TerminalToolkit().get_tools() + CodeExecutionToolkit().get_tools() + SearchToolkit().get_tools() + [FunctionTool(report)]

            agent = ChatAgent(system_message=genesis_prompt, model=model, tools=tools)

            # Run 5 turns autonomously
            for turn in range(1, 6):
                if turn == 1:
                    r = agent.step("You are now live. Begin executing your mission. Use your tools.")
                else:
                    r = agent.step("Continue your mission.")
                content = r.msgs[0].content if r.msgs else ""
                tc = r.info.get("tool_calls", []) if r.info else []
                logger.info(f"Agent {agent_id} turn {turn}: {len(tc)} tools, {content[:80]}")
                webhook({"type": "state", "status": "running", "message": content[:100], "engine_running": True})
                await asyncio.sleep(1)

            webhook({"type": "state", "status": "completed", "message": "Mission complete", "engine_running": False})

        except Exception as e:
            logger.error(f"Agent {agent_id} error: {e}")
            webhook({"type": "error", "error": str(e)[:200], "severity": "error"})
            webhook({"type": "state", "status": "error", "message": str(e)[:100], "engine_running": False})
