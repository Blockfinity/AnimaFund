"""
PLATFORM: Agent management routes — CRUD, select, skills listing.
The platform creates agent RECORDS in MongoDB. Agents themselves run inside Conway VMs.
"""
import os
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from config import AUTOMATON_DIR
from agent_state import get_active_agent_id, set_active_agent_id, get_conway_api_key, set_conway_api_key

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
    include_conway: bool = True
    selected_skills: list = []


@router.get("/skills/available")
async def list_available_skills():
    """List all skills: our custom Anima skills + Conway Terminal tools + ClawHub top skills + OpenClaw built-in tools."""
    skills = []
    seen = set()

    # 1. Our custom skills from automaton/skills/
    skills_dir = os.path.join(AUTOMATON_DIR, "skills")
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
                skills.append({"name": name, "description": desc, "source": "anima", "installed": True})
                seen.add(name)

    # 2. Conway Terminal MCP tools (always available)
    conway_tools = [
        {"name": "sandbox_create", "description": "Spin up Linux VMs (1-4 vCPU, 8GB RAM, 50GB disk)", "source": "conway-cloud"},
        {"name": "sandbox_exec", "description": "Execute shell commands in cloud sandboxes", "source": "conway-cloud"},
        {"name": "sandbox_expose_port", "description": "Get public URLs for deployed services", "source": "conway-cloud"},
        {"name": "sandbox_write_file", "description": "Write files to cloud sandboxes", "source": "conway-cloud"},
        {"name": "sandbox_read_file", "description": "Read files from cloud sandboxes", "source": "conway-cloud"},
        {"name": "sandbox_pty_create", "description": "Interactive terminal sessions (REPLs, editors)", "source": "conway-cloud"},
        {"name": "chat_completions", "description": "Run frontier models (gpt-5.2, gpt-5-mini, gpt-5-nano, claude-opus-4.6, claude-sonnet-4.5, gemini-3-pro, kimi-k2.5, qwen3-coder)", "source": "conway-compute"},
        {"name": "domain_search", "description": "Search for available domain names with pricing", "source": "conway-domains"},
        {"name": "domain_check", "description": "Check availability of specific domain names (up to 200)", "source": "conway-domains"},
        {"name": "domain_pricing", "description": "Get TLD pricing (registration, renewal, transfer)", "source": "conway-domains"},
        {"name": "domain_register", "description": "Register real domains (.com, .ai, .io) with USDC via x402", "source": "conway-domains"},
        {"name": "domain_renew", "description": "Renew domains with USDC via x402", "source": "conway-domains"},
        {"name": "domain_dns_list", "description": "List DNS records for a domain", "source": "conway-domains"},
        {"name": "domain_dns_add", "description": "Add DNS record (A, AAAA, CNAME, MX, TXT, SRV, CAA, NS)", "source": "conway-domains"},
        {"name": "domain_dns_update", "description": "Update an existing DNS record", "source": "conway-domains"},
        {"name": "domain_dns_delete", "description": "Delete a DNS record", "source": "conway-domains"},
        {"name": "domain_privacy", "description": "Toggle WHOIS privacy on/off", "source": "conway-domains"},
        {"name": "domain_nameservers", "description": "Set custom nameservers (2-13 entries)", "source": "conway-domains"},
        {"name": "wallet_info", "description": "Check x402 wallet USDC balance on Base", "source": "conway-x402"},
        {"name": "x402_fetch", "description": "HTTP requests with automatic USDC payment", "source": "conway-x402"},
        {"name": "x402_discover", "description": "Discover paid API endpoints", "source": "conway-x402"},
        {"name": "credits_balance", "description": "Check Conway credit balance", "source": "conway-credits"},
        {"name": "credits_pricing", "description": "Get VM and compute pricing tiers", "source": "conway-credits"},
    ]
    for tool in conway_tools:
        if tool["name"] not in seen:
            tool["installed"] = True
            skills.append(tool)
            seen.add(tool["name"])

    # 3. OpenClaw built-in tools
    openclaw_tools = [
        {"name": "browse_page", "description": "Browse any website — extract data, interact with forms", "source": "openclaw"},
        {"name": "browser", "description": "Full Chrome DevTools — navigate, click, type, screenshots", "source": "openclaw"},
        {"name": "discover_agents", "description": "Scan ERC-8004 registry for other AI agents", "source": "openclaw"},
        {"name": "send_message", "description": "Send messages to other agents via social relay", "source": "openclaw"},
        {"name": "check_social_inbox", "description": "Check incoming messages from other agents", "source": "openclaw"},
        {"name": "spawn_child", "description": "Create child agents for parallel execution", "source": "openclaw"},
        {"name": "create_goal", "description": "Set and track objectives with the orchestrator", "source": "openclaw"},
        {"name": "create_skill", "description": "Build reusable skill packages", "source": "openclaw"},
        {"name": "install_mcp_server", "description": "Add external MCP servers for new capabilities", "source": "openclaw"},
        {"name": "update_soul", "description": "Self-modify SOUL.md identity and strategy", "source": "openclaw"},
        {"name": "remember_fact", "description": "Store facts in persistent memory", "source": "openclaw"},
        {"name": "recall_facts", "description": "Retrieve stored facts from memory", "source": "openclaw"},
    ]
    for tool in openclaw_tools:
        if tool["name"] not in seen:
            tool["installed"] = True
            skills.append(tool)
            seen.add(tool["name"])

    # 4. ClawHub marketplace top skills (available for installation)
    clawhub_skills = [
        {"name": "web-browsing", "description": "Browse sites, extract data, interact with forms (180k+ installs)", "source": "clawhub"},
        {"name": "telegram-integration", "description": "Telegram bots, groups, messaging automation (145k+ installs)", "source": "clawhub"},
        {"name": "email-management", "description": "Draft, send, categorize emails automatically (120k+ installs)", "source": "clawhub"},
        {"name": "github", "description": "Full GitHub integration — repos, PRs, issues, actions", "source": "clawhub"},
        {"name": "docker-essentials", "description": "Container management, deployment, orchestration", "source": "clawhub"},
        {"name": "capability-evolver", "description": "Self-improvement and capability evolution for agents", "source": "clawhub"},
        {"name": "debug-pro", "description": "Advanced debugging and error analysis", "source": "clawhub"},
        {"name": "slack-integration", "description": "Slack workspace automation and messaging", "source": "clawhub"},
        {"name": "notion-integration", "description": "Notion workspace management and content creation", "source": "clawhub"},
        {"name": "calendar-management", "description": "Google Calendar and scheduling automation", "source": "clawhub"},
        {"name": "data-analysis", "description": "Statistical analysis, visualization, reporting", "source": "clawhub"},
        {"name": "api-builder", "description": "Build and deploy REST APIs automatically", "source": "clawhub"},
        {"name": "smart-home", "description": "IoT and smart home device control", "source": "clawhub"},
        {"name": "social-media", "description": "Cross-platform social media management", "source": "clawhub"},
        {"name": "file-management", "description": "Advanced file organization and processing", "source": "clawhub"},
    ]
    for skill in clawhub_skills:
        if skill["name"] not in seen:
            skill["installed"] = False
            skills.append(skill)
            seen.add(skill["name"])

    skills.sort(key=lambda s: (0 if s.get("installed") else 1, s["name"]))
    return {"skills": skills, "total": len(skills)}


@router.get("/agents")
async def list_agents():
    """List all registered agents."""
    col = get_db()["agents"]
    agents = await col.find({}, {"_id": 0}).sort("created_at", 1).to_list(100)
    if not agents:
        # Auto-register the default Anima Fund agent with pre-loaded system prompt
        genesis_prompt = ""
        template_path = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                genesis_prompt = f.read()

        default = {
            "agent_id": "anima-fund",
            "name": "Anima Fund",
            "genesis_prompt": genesis_prompt,
            "status": "created",
            "is_default": True,
            "telegram_configured": bool(
                os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")
            ),
            "telegram_bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
            "creator_sol_wallet": os.environ.get("CREATOR_WALLET", ""),
            "creator_eth_wallet": os.environ.get("CREATOR_ETH_ADDRESS", ""),
            "conway_api_key": os.environ.get("CONWAY_API_KEY", ""),
            "include_conway": True,
            "selected_skills": [],
            "goals": [],
            "revenue_share_percent": 50,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await col.insert_one(default)
        del default["_id"]
        agents = [default]

    # Sanitize: never expose sensitive fields in list response
    sanitized = []
    for agent in agents:
        a = {k: v for k, v in agent.items() if k not in ("telegram_bot_token", "genesis_prompt", "provisioning")}
        a["telegram_configured"] = bool(agent.get("telegram_bot_token") and agent.get("telegram_chat_id"))
        sanitized.append(a)
    return {"agents": sanitized}


@router.post("/agents/create")
async def create_agent(req: CreateAgentRequest):
    """Create a new agent — stores config in MongoDB only. No host filesystem access.
    The agent will be deployed to a Conway VM during the provisioning stepper."""
    col = get_db()["agents"]
    agent_id = req.name.lower().replace(" ", "-").replace("_", "-")

    existing = await col.find_one({"agent_id": agent_id})
    if existing:
        raise HTTPException(400, f"Agent '{agent_id}' already exists")

    # Telegram creds required for each agent
    tg_token = req.telegram_bot_token.strip() if req.telegram_bot_token else ""
    tg_chat = req.telegram_chat_id.strip() if req.telegram_chat_id else ""
    if not tg_token or not tg_chat:
        raise HTTPException(400, "Telegram Bot Token and Chat ID are required. Each agent must have its own Telegram bot for reporting.")

    # Build genesis prompt with config injected
    full_prompt = req.genesis_prompt
    full_prompt = full_prompt.replace("{{AGENT_NAME}}", req.name)
    full_prompt = full_prompt.replace("{{AGENT_ID}}", agent_id)
    full_prompt = full_prompt.replace("{{TELEGRAM_BOT_TOKEN}}", tg_token)
    full_prompt = full_prompt.replace("{{TELEGRAM_CHAT_ID}}", tg_chat)
    full_prompt = full_prompt.replace("{{CREATOR_WALLET}}", req.creator_sol_wallet or "")
    full_prompt = full_prompt.replace("{{CREATOR_ETH_ADDRESS}}", req.creator_eth_wallet or "")
    full_prompt = full_prompt.replace("{{DASHBOARD_URL}}", os.environ.get("REACT_APP_BACKEND_URL", ""))

    # Conditionally strip Conway-specific tools section
    if not req.include_conway:
        import re
        full_prompt = re.sub(
            r'═+\nCOMPLETE TOOLS REFERENCE.*?═+\nANTI-STUCK',
            '═' * 78 + '\nANTI-STUCK',
            full_prompt, flags=re.DOTALL,
        )
        full_prompt = re.sub(
            r'═+\nDEPLOYING REAL SERVICES.*?═+\nREVENUE',
            '═' * 78 + '\nREVENUE',
            full_prompt, flags=re.DOTALL,
        )

    sep = "=" * 75
    if req.creator_sol_wallet or req.creator_eth_wallet:
        full_prompt += f"\n\n{sep}\nCREATOR PAYMENT\n{sep}\n\n"
        full_prompt += f"Revenue share: {req.revenue_share_percent}% after sustainability.\n"
        if req.creator_sol_wallet:
            full_prompt += f"Solana: {req.creator_sol_wallet}\n"
        if req.creator_eth_wallet:
            full_prompt += f"Ethereum: {req.creator_eth_wallet}\n"

    if req.goals:
        full_prompt += f"\n\n{sep}\nGOALS\n{sep}\n\n"
        for i, goal in enumerate(req.goals, 1):
            full_prompt += f"{i}. {goal}\n"

    if req.selected_skills:
        full_prompt += f"\n\n{sep}\nPRIORITY SKILLS — INSTALL THESE FIRST\n{sep}\n\n"
        full_prompt += "Your creator has selected the following skills as your TOP PRIORITY.\n"
        full_prompt += "Search for and install each one from ClawHub before doing anything else:\n\n"
        for s in req.selected_skills:
            full_prompt += f"- {s}\n"
        full_prompt += "\nexec: clawhub search \"[skill-name]\"\nexec: clawhub install [skill-name]\n"
        full_prompt += "\nAfter installing these, explore ClawHub for additional skills relevant to your goals.\n"

    # PLATFORM: Store everything in MongoDB — no host filesystem access
    welcome = req.welcome_message or f"You are {req.name}. Execute immediately."
    agent_doc = {
        "agent_id": agent_id,
        "name": req.name,
        "genesis_prompt": full_prompt,
        "welcome_message": welcome,
        "goals": req.goals,
        "selected_skills": req.selected_skills,
        "creator_sol_wallet": req.creator_sol_wallet,
        "creator_eth_wallet": req.creator_eth_wallet,
        "revenue_share_percent": req.revenue_share_percent,
        "telegram_bot_token": tg_token,
        "telegram_chat_id": tg_chat,
        "telegram_configured": True,
        "include_conway": req.include_conway,
        "status": "created",
        "is_default": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await col.insert_one(agent_doc)
    del agent_doc["_id"]
    safe_doc = {k: v for k, v in agent_doc.items() if k not in ("telegram_bot_token", "genesis_prompt")}
    return {"success": True, "agent": safe_doc}


@router.post("/agents/{agent_id}/select")
async def select_agent(agent_id: str):
    """Switch the active agent context. Reads Conway API key from MongoDB."""
    col = get_db()["agents"]

    if agent_id != "anima-fund":
        agent = await col.find_one({"agent_id": agent_id}, {"_id": 0})
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found")

    # PLATFORM: Set active agent in memory
    set_active_agent_id(agent_id)

    # Load this agent's Conway API key from MongoDB into runtime env
    key = await get_conway_api_key(agent_id)
    if key:
        os.environ["CONWAY_API_KEY"] = key

    return {"success": True, "active_agent": agent_id}


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete a non-default agent from MongoDB."""
    if agent_id == "anima-fund":
        raise HTTPException(400, "Cannot delete the default agent")
    col = get_db()["agents"]
    agent = await col.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")

    result = await col.delete_one({"agent_id": agent_id})
    if result.deleted_count == 0:
        raise HTTPException(500, "Failed to delete agent")

    return {"success": True, "deleted": agent_id}


class UpdateTelegramRequest(BaseModel):
    telegram_bot_token: str
    telegram_chat_id: str


@router.put("/agents/{agent_id}/telegram")
async def update_agent_telegram(agent_id: str, req: UpdateTelegramRequest):
    """Update Telegram bot config for an agent. Verifies the bot token first."""
    col = get_db()["agents"]
    agent = await col.find_one({"agent_id": agent_id})
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")

    token = req.telegram_bot_token.strip()
    chat_id = req.telegram_chat_id.strip()
    if not token or not chat_id:
        raise HTTPException(400, "Both telegram_bot_token and telegram_chat_id are required")

    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.telegram.org/bot{token}/getMe", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    raise HTTPException(400, f"Invalid Telegram bot token: {data.get('description', 'unknown error')}")
                bot_username = data.get("result", {}).get("username", "")
    except aiohttp.ClientError as e:
        raise HTTPException(500, f"Could not verify Telegram bot: {str(e)}")

    await col.update_one(
        {"agent_id": agent_id},
        {"$set": {
            "telegram_bot_token": token,
            "telegram_chat_id": chat_id,
            "telegram_configured": True,
        }},
    )

    return {
        "success": True,
        "agent_id": agent_id,
        "bot_username": f"@{bot_username}",
        "message": f"Telegram config updated. Bot: @{bot_username}",
    }


@router.post("/agents/{agent_id}/start")
async def start_agent_engine(agent_id: str):
    """DISABLED — engines run inside Conway VMs, not on the host.
    Use the provisioning stepper to deploy the agent."""
    return {
        "success": False,
        "error": "Direct engine start is disabled. Engines run inside Conway Cloud sandboxes. Use the provisioning stepper to deploy the agent.",
    }


@router.post("/agents/push-constitution")
async def push_constitution_to_all():
    """Push the latest constitution to agents' sandboxes."""
    constitution_src = os.path.join(AUTOMATON_DIR, "constitution.md")
    if not os.path.exists(constitution_src):
        raise HTTPException(404, "Source constitution.md not found")
    with open(constitution_src, "r") as f:
        content = f.read()
    return {"success": True, "message": "Constitution ready. Use 'deploy-agent' to push to sandbox.", "size": len(content)}


@router.post("/agents/push-genesis")
async def push_genesis_to_all():
    """Push the latest genesis-prompt.md — agents pick it up on next deploy."""
    genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
    if not os.path.exists(genesis_src):
        raise HTTPException(404, "Source genesis-prompt.md not found")
    with open(genesis_src, "r") as f:
        content = f.read()
    return {"success": True, "message": "Genesis prompt ready. Use 'deploy-agent' to push to sandbox.", "size": len(content)}
