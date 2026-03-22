"""
Ultimus Executor — Converts simulation personas into REAL deployed agents.
Each genesis prompt is built from THAT PERSONA'S specific behavioral history,
relationships, and strategies from the simulation — not a generic template.
Agents run as SEPARATE PROCESSES with isolated environments.
"""
import os
import sys
import json
import subprocess
import logging
import secrets
from datetime import datetime, timezone
from typing import Dict, List

logger = logging.getLogger(__name__)


class Executor:
    """Deploys real Anima agents from simulation results.
    Each agent runs as a separate subprocess — NOT asyncio tasks in the platform process."""

    _processes: Dict[str, subprocess.Popen] = {}

    async def execute(self, prediction_id: str, strategy: Dict, goal: str,
                      cost_model: Dict, db=None) -> Dict:
        """Deploy real agents from a completed prediction."""
        # Get the full prediction with per-persona data
        pred = None
        if db is not None:
            pred = await db.predictions.find_one({"id": prediction_id}, {"_id": 0})
        if not pred:
            return {"error": "Prediction not found"}

        personas = pred.get("personas", [])
        round_summaries = pred.get("round_summaries", [])
        relationships = pred.get("relationships", [])
        recommended = strategy.get("recommended_agents", [])

        if not personas:
            return {"error": "No personas in prediction"}

        # Match recommended agents to simulation personas
        deployed = []
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "")

        for agent_spec in recommended[:10]:
            role = agent_spec.get("role", "Agent")
            # Find the matching persona from the simulation
            persona = self._find_matching_persona(role, personas)
            if not persona:
                continue

            # Build per-persona genesis prompt from THEIR behavioral history
            genesis = self._build_genesis_from_persona(
                persona, goal, round_summaries, relationships, personas, strategy
            )

            agent_id = f"anima-{role.lower().replace(' ', '-')[:20]}-{secrets.token_hex(3)}"
            webhook_token = secrets.token_hex(16)

            agent_record = {
                "agent_id": agent_id,
                "name": persona.get("name", role),
                "role": role,
                "genesis_prompt": genesis,
                "prediction_id": prediction_id,
                "status": "running",
                "provisioning": {"webhook_token": webhook_token},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            if db is not None:
                await db.agents.update_one({"agent_id": agent_id}, {"$set": agent_record}, upsert=True)

            # Start as a SEPARATE PROCESS — not asyncio task
            proc = self._spawn_agent_process(agent_id, genesis, webhook_token, api_url)
            if proc:
                self._processes[agent_id] = proc
                deployed.append({"agent_id": agent_id, "name": persona.get("name"), "role": role, "status": "running", "pid": proc.pid})
            else:
                deployed.append({"agent_id": agent_id, "name": persona.get("name"), "role": role, "status": "failed"})

        return {
            "prediction_id": prediction_id,
            "agents_created": len(deployed),
            "agents": deployed,
        }

    def _find_matching_persona(self, role: str, personas: List[Dict]) -> Dict:
        """Find the simulation persona that matches this role."""
        role_lower = role.lower()
        for p in personas:
            if role_lower in (p.get("role", "") or "").lower() or role_lower in (p.get("name", "") or "").lower():
                return p
        # Fuzzy: match on key words
        role_words = set(role_lower.split())
        best, best_score = None, 0
        for p in personas:
            p_words = set((p.get("role", "") + " " + p.get("name", "")).lower().split())
            score = len(role_words & p_words)
            if score > best_score:
                best, best_score = p, score
        return best or (personas[0] if personas else {})

    def _build_genesis_from_persona(self, persona: Dict, goal: str,
                                     round_summaries: List[Dict],
                                     relationships: List[Dict],
                                     all_personas: List[Dict],
                                     strategy: Dict) -> str:
        """Build a genesis prompt from THIS PERSONA'S specific simulation data."""
        name = persona.get("name", "Agent")
        role = persona.get("role", "")
        personality = persona.get("personality", "")
        strat = persona.get("strategy", "")

        # Extract THIS persona's actions across all rounds
        my_actions = []
        for rs in round_summaries:
            pos = rs.get("positions", {}).get(name, "")
            if pos:
                my_actions.append(f"Round {rs['round']}: {pos}")

        # Extract THIS persona's relationships
        my_allies = []
        my_opponents = []
        for r in relationships:
            if r["from"] == name:
                if r["type"] in ("agrees_with", "builds_on"):
                    my_allies.append(r["to"])
                elif r["type"] == "disagrees_with":
                    my_opponents.append(r["to"])
            elif r["to"] == name:
                if r["type"] in ("agrees_with", "builds_on"):
                    my_allies.append(r["from"])
                elif r["type"] == "disagrees_with":
                    my_opponents.append(r["from"])

        allies = list(set(my_allies))
        opponents = list(set(my_opponents))

        # Build the genesis prompt
        genesis = f"""You are {name}, a {role}.

MISSION: {goal}

YOUR PERSONALITY: {personality}

YOUR STRATEGY (from simulation): {strat}

"""
        if my_actions:
            genesis += "YOUR BEHAVIORAL HISTORY (what you did in the simulation):\n"
            for a in my_actions[-5:]:
                genesis += f"  {a}\n"
            genesis += "\n"

        if allies:
            genesis += f"YOUR ALLIES (coordinate with them): {', '.join(allies)}\n"
        if opponents:
            genesis += f"YOUR OPPONENTS (monitor their moves): {', '.join(opponents)}\n"
        if allies or opponents:
            genesis += "\n"

        genesis += f"""OVERALL STRATEGY CONTEXT: {strategy.get('summary', '')}

TOOLS AVAILABLE: terminal (shell_exec), code execution (execute_code), web search (search_duckduckgo), file operations, state reporting

INSTRUCTIONS:
1. Begin executing your strategy IMMEDIATELY
2. Use report_state to report what you're doing
3. Use report_action after every significant action
4. Coordinate with allies, monitor opponents
5. Adapt your strategy based on what you discover
6. You operate AUTONOMOUSLY — no human input after boot
"""
        return genesis

    def _spawn_agent_process(self, agent_id: str, genesis: str, webhook_token: str, api_url: str) -> subprocess.Popen:
        """Spawn agent as a SEPARATE PROCESS — isolated from the platform server."""
        # Write genesis prompt and config to a temp directory for this agent
        agent_dir = f"/tmp/anima-agents/{agent_id}"
        os.makedirs(agent_dir, exist_ok=True)

        with open(f"{agent_dir}/genesis.md", "w") as f:
            f.write(genesis)

        with open(f"{agent_dir}/config.json", "w") as f:
            json.dump({
                "agent_id": agent_id,
                "webhook_url": f"{api_url}/api/webhook/agent-update",
                "webhook_token": webhook_token,
                "max_turns": 5,
            }, f)

        # Start as subprocess — separate process, separate environment
        env = os.environ.copy()
        env["AGENT_ID"] = agent_id
        env["AGENT_DIR"] = agent_dir

        try:
            proc = subprocess.Popen(
                [sys.executable, "/app/engine/agent_process.py", agent_dir],
                env=env,
                stdout=open(f"{agent_dir}/stdout.log", "w"),
                stderr=open(f"{agent_dir}/stderr.log", "w"),
                cwd=agent_dir,
            )
            logger.info(f"Agent {agent_id} spawned as PID {proc.pid}")
            return proc
        except Exception as e:
            logger.error(f"Failed to spawn {agent_id}: {e}")
            return None

    def kill_agent(self, agent_id: str) -> bool:
        """Kill a running agent process and clean up."""
        proc = self._processes.get(agent_id)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            logger.info(f"Agent {agent_id} terminated (PID {proc.pid})")
            return True
        return False

    def get_agent_status(self, agent_id: str) -> Dict:
        """Check if an agent process is alive."""
        proc = self._processes.get(agent_id)
        if not proc:
            return {"agent_id": agent_id, "status": "not_found"}
        returncode = proc.poll()
        if returncode is None:
            return {"agent_id": agent_id, "status": "running", "pid": proc.pid}
        return {"agent_id": agent_id, "status": "exited", "exit_code": returncode, "pid": proc.pid}

    def list_agents(self) -> List[Dict]:
        """List all managed agent processes."""
        return [self.get_agent_status(aid) for aid in self._processes]

    def kill_all(self):
        """Kill all running agents."""
        for aid in list(self._processes.keys()):
            self.kill_agent(aid)
