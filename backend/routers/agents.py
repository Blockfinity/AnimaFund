"""
Agent management routes — CRUD, select, start, skills listing.
"""
import os
import json
import subprocess
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from config import AUTOMATON_DIR
from engine_bridge import set_active_data_dir

router = APIRouter(prefix="/api", tags=["agents"])


class CreateAgentRequest(BaseModel):
    name: str
    genesis_prompt: str
    welcome_message: str = ""
    goals: list = []
    creator_sol_wallet: str = ""
    creator_eth_wallet: str = ""
    revenue_share_percent: int = 50
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    selected_skills: list = []  # Empty = copy all skills


@router.get("/skills/available")
async def list_available_skills():
    """List all skills available in the automaton skills directory for the agent creator."""
    skills_dir = os.path.join(AUTOMATON_DIR, "skills")
    skills = []
    if os.path.isdir(skills_dir):
        for name in sorted(os.listdir(skills_dir)):
            skill_file = os.path.join(skills_dir, name, "SKILL.md")
            if os.path.exists(skill_file):
                desc = ""
                with open(skill_file, "r") as f:
                    for line in f:
                        if line.startswith("description:"):
                            desc = line.split(":", 1)[1].strip()
                            break
                skills.append({"name": name, "description": desc})
    return {"skills": skills, "total": len(skills)}


@router.get("/agents")
async def list_agents():
    """List all registered agents."""
    col = get_db()["agents"]
    agents = await col.find({}, {"_id": 0}).sort("created_at", 1).to_list(100)
    if not agents:
        # Auto-register the default Anima Fund agent
        default = {
            "agent_id": "anima-fund",
            "name": "Anima Fund",
            "data_dir": "~/.anima",
            "status": "running",
            "is_default": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await col.insert_one(default)
        del default["_id"]
        agents = [default]
    return {"agents": agents}


@router.post("/agents/create")
async def create_agent(req: CreateAgentRequest):
    """Create a new agent with its own data directory, genesis prompt, goals, and financial config."""
    col = get_db()["agents"]
    agent_id = req.name.lower().replace(" ", "-").replace("_", "-")

    # Check if agent already exists
    existing = await col.find_one({"agent_id": agent_id})
    if existing:
        raise HTTPException(400, f"Agent '{agent_id}' already exists")

    # Each agent gets its own HOME directory so engine reads from $HOME/.automaton/
    agent_home = os.path.expanduser(f"~/agents/{agent_id}")
    automaton_dir = os.path.join(agent_home, ".automaton")
    skills_dir = os.path.join(automaton_dir, "skills")
    os.makedirs(skills_dir, exist_ok=True)

    # Per-agent Telegram creds, fallback to global
    tg_token = req.telegram_bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    tg_chat = req.telegram_chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")

    # Build full genesis prompt with all config injected
    full_prompt = req.genesis_prompt
    full_prompt = full_prompt.replace("{{TELEGRAM_BOT_TOKEN}}", tg_token)
    full_prompt = full_prompt.replace("{{TELEGRAM_CHAT_ID}}", tg_chat)

    sep = "=" * 75
    if req.creator_sol_wallet or req.creator_eth_wallet:
        full_prompt += f"\n\n{sep}\nCREATOR PAYMENT\n{sep}\n\n"
        full_prompt += f"Revenue share: {req.revenue_share_percent}% after sustainability.\n"
        if req.creator_sol_wallet:
            full_prompt += f"Solana: {req.creator_sol_wallet}\n"
        if req.creator_eth_wallet:
            full_prompt += f"Ethereum: {req.creator_eth_wallet}\n"

    if tg_token and tg_chat:
        full_prompt += f"\n\n{sep}\nTELEGRAM\n{sep}\n\n"
        full_prompt += f'Report EVERY turn via Telegram bot token: {tg_token}, chat: {tg_chat}\n'

    if req.goals:
        full_prompt += f"\n\n{sep}\nGOALS\n{sep}\n\n"
        for i, goal in enumerate(req.goals, 1):
            full_prompt += f"{i}. {goal}\n"

    # Write genesis prompt into agent's .automaton/
    with open(os.path.join(automaton_dir, "genesis-prompt.md"), "w") as f:
        f.write(full_prompt)

    # Write auto-config.json for non-interactive engine setup
    welcome = req.welcome_message or f"You are {req.name}. Execute immediately."
    with open(os.path.join(automaton_dir, "auto-config.json"), "w") as f:
        json.dump({
            "name": req.name,
            "genesisPrompt": full_prompt,
            "creatorMessage": welcome,
            "creatorAddress": "0x0000000000000000000000000000000000000000",
        }, f)

    # Copy constitution (contains security rules — Article XIII)
    constitution_src = os.path.join(AUTOMATON_DIR, "constitution.md")
    if os.path.exists(constitution_src):
        import shutil
        shutil.copy2(constitution_src, os.path.join(automaton_dir, "constitution.md"))

    # Copy skills — only selected, or all if none specified
    src_skills = os.path.join(AUTOMATON_DIR, "skills")
    if os.path.isdir(src_skills):
        selected = set(req.selected_skills) if req.selected_skills else None
        for sname in os.listdir(src_skills):
            if selected and sname not in selected:
                continue
            sf = os.path.join(src_skills, sname, "SKILL.md")
            if os.path.exists(sf):
                td = os.path.join(skills_dir, sname)
                os.makedirs(td, exist_ok=True)
                with open(sf, "r") as f:
                    skill_content = f.read()
                skill_content = skill_content.replace("{{TELEGRAM_BOT_TOKEN}}", tg_token)
                skill_content = skill_content.replace("{{TELEGRAM_CHAT_ID}}", tg_chat)
                with open(os.path.join(td, "SKILL.md"), "w") as f:
                    f.write(skill_content)

    agent_doc = {
        "agent_id": agent_id,
        "name": req.name,
        "agent_home": agent_home,
        "data_dir": automaton_dir,
        "welcome_message": welcome,
        "goals": req.goals,
        "creator_sol_wallet": req.creator_sol_wallet,
        "creator_eth_wallet": req.creator_eth_wallet,
        "revenue_share_percent": req.revenue_share_percent,
        "telegram_configured": bool(tg_token),
        "status": "created",
        "is_default": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await col.insert_one(agent_doc)
    del agent_doc["_id"]
    return {"success": True, "agent": agent_doc}


@router.post("/agents/{agent_id}/select")
async def select_agent(agent_id: str):
    """Switch the dashboard to view a different agent's data."""
    col = get_db()["agents"]

    if agent_id == "anima-fund":
        set_active_data_dir("~/.anima")
        return {"success": True, "active_agent": agent_id, "data_dir": "~/.anima"}

    agent = await col.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")

    # New agents use $HOME/.automaton pattern
    data_dir = agent.get("data_dir", "")
    if data_dir:
        set_active_data_dir(data_dir)
    else:
        agent_home = agent.get("agent_home", os.path.expanduser(f"~/agents/{agent_id}"))
        automaton_dir = os.path.join(agent_home, ".automaton")
        set_active_data_dir(automaton_dir)
        data_dir = automaton_dir

    return {"success": True, "active_agent": agent_id, "data_dir": data_dir}


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete a non-default agent."""
    if agent_id == "anima-fund":
        raise HTTPException(400, "Cannot delete the default agent")
    col = get_db()["agents"]
    result = await col.delete_one({"agent_id": agent_id})
    if result.deleted_count == 0:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    return {"success": True}


@router.post("/agents/{agent_id}/start")
async def start_agent_engine(agent_id: str):
    """Start the engine for a specific agent using isolated HOME directory."""
    col = get_db()["agents"]
    agent = await col.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")

    agent_home = os.path.expanduser(agent.get("agent_home", f"~/agents/{agent_id}"))
    automaton_dir = os.path.join(agent_home, ".automaton")

    if not os.path.exists(os.path.join(automaton_dir, "auto-config.json")):
        raise HTTPException(400, "No auto-config found. Agent not properly set up.")

    # Start engine with HOME set to agent's home dir so it reads $HOME/.automaton/
    engine_script = os.path.join(os.path.dirname(__file__), "..", "scripts", "start_engine.sh")
    log_out = os.path.join(agent_home, "engine.out.log")
    log_err = os.path.join(agent_home, "engine.err.log")

    env = os.environ.copy()
    env["HOME"] = agent_home

    try:
        with open(log_out, "a") as fout, open(log_err, "a") as ferr:
            proc = subprocess.Popen(
                ["bash", engine_script],
                env=env,
                stdout=fout,
                stderr=ferr,
                cwd=os.path.join(os.path.dirname(__file__), ".."),
            )
        await col.update_one({"agent_id": agent_id}, {"$set": {"status": "running", "engine_pid": proc.pid}})
        return {"success": True, "pid": proc.pid, "home": agent_home}
    except Exception as e:
        raise HTTPException(500, f"Failed to start engine: {str(e)}")


@router.post("/agents/push-constitution")
async def push_constitution_to_all():
    """Push the latest constitution to ALL existing agents without resetting them.
    This updates the constitution file in each agent's data directory in-place.
    Running agents will pick it up on their next constitution read."""
    import shutil
    constitution_src = os.path.join(AUTOMATON_DIR, "constitution.md")
    if not os.path.exists(constitution_src):
        raise HTTPException(404, "Source constitution.md not found")

    col = get_db()["agents"]
    agents = await col.find({}, {"_id": 0}).to_list(100)
    updated = []

    for agent in agents:
        agent_id = agent.get("agent_id", "")
        if agent_id == "anima-fund":
            # Default agent uses ~/.anima
            target_dir = os.path.expanduser("~/.anima")
        else:
            data_dir = agent.get("data_dir", "")
            if data_dir:
                target_dir = os.path.expanduser(data_dir)
            else:
                target_dir = os.path.expanduser(f"~/agents/{agent_id}/.automaton")

        if os.path.isdir(target_dir):
            target_path = os.path.join(target_dir, "constitution.md")
            shutil.copy2(constitution_src, target_path)
            updated.append(agent_id)

    return {
        "success": True,
        "updated_agents": updated,
        "total": len(updated),
        "message": "Constitution pushed to all agents. Running agents will pick up changes on next read.",
    }
