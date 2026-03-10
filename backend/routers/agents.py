"""
Agent management routes — CRUD, select, skills listing.
All agent operations happen inside Conway Cloud sandbox. Nothing on host.
"""
import os
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from config import AUTOMATON_DIR

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
    include_conway: bool = True  # Include Conway Terminal tools in genesis prompt
    selected_skills: list = []  # Skills the agent should prioritize installing first


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
            skill["installed"] = False  # Available for install from marketplace
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
        # Auto-register the default Anima Fund agent
        default = {
            "agent_id": "anima-fund",
            "name": "Anima Fund",
            "data_dir": "~/.anima",
            "status": "running",
            "is_default": True,
            "telegram_configured": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await col.insert_one(default)
        del default["_id"]
        agents = [default]

    # Sanitize: never expose telegram_bot_token in the list response
    sanitized = []
    for agent in agents:
        a = {k: v for k, v in agent.items() if k != "telegram_bot_token"}
        # For the default agent, check env vars for Telegram config
        if agent.get("is_default"):
            a["telegram_configured"] = bool(
                os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")
            )
        elif "telegram_configured" not in a:
            a["telegram_configured"] = bool(agent.get("telegram_bot_token") and agent.get("telegram_chat_id"))
        sanitized.append(a)
    return {"agents": sanitized}


@router.post("/agents/create")
async def create_agent(req: CreateAgentRequest):
    """Create a new agent with its own data directory, genesis prompt, goals, and financial config."""
    col = get_db()["agents"]
    agent_id = req.name.lower().replace(" ", "-").replace("_", "-")

    # Check if agent already exists
    existing = await col.find_one({"agent_id": agent_id})
    if existing:
        raise HTTPException(400, f"Agent '{agent_id}' already exists")

    # Each agent gets its own HOME directory so engine reads from $HOME/.anima/
    # The engine's getAutomatonDir() returns $HOME/.anima
    # We create .anima as main dir, .automaton as symlink for compatibility
    agent_home = os.path.expanduser(f"~/agents/{agent_id}")
    anima_dir = os.path.join(agent_home, ".anima")
    automaton_link = os.path.join(agent_home, ".automaton")
    os.makedirs(anima_dir, exist_ok=True)
    if not os.path.exists(automaton_link):
        os.symlink(".anima", automaton_link)
    automaton_dir = anima_dir  # Use .anima as the actual data directory

    # Per-agent Telegram creds — REQUIRED for new agents (no global fallback)
    tg_token = req.telegram_bot_token.strip() if req.telegram_bot_token else ""
    tg_chat = req.telegram_chat_id.strip() if req.telegram_chat_id else ""
    if not tg_token or not tg_chat:
        raise HTTPException(400, "Telegram Bot Token and Chat ID are required. Each agent must have its own Telegram bot for reporting.")

    # Build full genesis prompt with all config injected
    full_prompt = req.genesis_prompt
    full_prompt = full_prompt.replace("{{AGENT_NAME}}", req.name)
    full_prompt = full_prompt.replace("{{AGENT_ID}}", agent_id)
    full_prompt = full_prompt.replace("{{TELEGRAM_BOT_TOKEN}}", tg_token)
    full_prompt = full_prompt.replace("{{TELEGRAM_CHAT_ID}}", tg_chat)
    full_prompt = full_prompt.replace("{{CREATOR_WALLET}}", req.creator_sol_wallet or "")
    full_prompt = full_prompt.replace("{{CREATOR_ETH_ADDRESS}}", req.creator_eth_wallet or "")
    # Dashboard webhook URL — the agent sends logs here directly
    dashboard_url = os.environ.get("DASHBOARD_URL", os.environ.get("REACT_APP_BACKEND_URL", ""))
    full_prompt = full_prompt.replace("{{DASHBOARD_URL}}", dashboard_url)

    # Conditionally strip Conway-specific tools section if agent doesn't want Conway
    if not req.include_conway:
        import re
        # Remove the COMPLETE TOOLS REFERENCE section (Conway-specific tools)
        full_prompt = re.sub(
            r'═+\nCOMPLETE TOOLS REFERENCE.*?═+\nANTI-STUCK',
            '═' * 78 + '\nANTI-STUCK',
            full_prompt,
            flags=re.DOTALL,
        )
        # Remove the DEPLOYING REAL SERVICES section (relies on Conway sandboxes)
        full_prompt = re.sub(
            r'═+\nDEPLOYING REAL SERVICES.*?═+\nREVENUE',
            '═' * 78 + '\nREVENUE',
            full_prompt,
            flags=re.DOTALL,
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

    # Inject priority skills — these are skills the agent should discover and install FIRST
    if req.selected_skills:
        full_prompt += f"\n\n{sep}\nPRIORITY SKILLS — INSTALL THESE FIRST\n{sep}\n\n"
        full_prompt += "Your creator has selected the following skills as your TOP PRIORITY.\n"
        full_prompt += "Search for and install each one from ClawHub before doing anything else:\n\n"
        for s in req.selected_skills:
            full_prompt += f"- {s}\n"
        full_prompt += "\nexec: clawhub search \"[skill-name]\"\nexec: clawhub install [skill-name]\n"
        full_prompt += "\nAfter installing these, explore ClawHub for additional skills relevant to your goals.\n"

    # Write genesis prompt — this is the ONLY instruction the agent needs.
    # The agent is fully autonomous and will install its own tools, skills, and environment.
    with open(os.path.join(automaton_dir, "genesis-prompt.md"), "w") as f:
        f.write(full_prompt)

    # Write auto-config.json for non-interactive engine setup
    welcome = req.welcome_message or f"You are {req.name}. Execute immediately."
    creator_addr = req.creator_eth_wallet or "0x0000000000000000000000000000000000000000"
    with open(os.path.join(automaton_dir, "auto-config.json"), "w") as f:
        json.dump({
            "name": req.name,
            "genesisPrompt": full_prompt,
            "creatorMessage": welcome,
            "creatorAddress": creator_addr,
        }, f)

    # Agent will be provisioned via the sandbox stepper — no host bootstrap needed.
    agent_doc = {
        "agent_id": agent_id,
        "name": req.name,
        "agent_home": agent_home,
        "data_dir": anima_dir,
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
    # Don't expose token in response
    safe_doc = {k: v for k, v in agent_doc.items() if k != "telegram_bot_token"}
    return {"success": True, "agent": safe_doc}


@router.post("/agents/{agent_id}/select")
async def select_agent(agent_id: str):
    """Switch the dashboard to view a different agent's data.
    Also switches the active Conway API key to that agent's key."""
    col = get_db()["agents"]

    # Write active agent ID
    with open("/tmp/anima_active_agent_id", "w") as f:
        f.write(agent_id)

    if agent_id == "anima-fund":
        # Load the default agent's key
        home = os.path.expanduser("~")
        prov_path = os.path.join(home, ".anima", "provisioning-status.json")
    else:
        agent = await col.find_one({"agent_id": agent_id}, {"_id": 0})
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found")
        home = os.path.expanduser("~")
        prov_path = os.path.join(home, "agents", agent_id, ".anima", "provisioning-status.json")

    # Switch Conway API key to the selected agent's key
    try:
        if os.path.exists(prov_path):
            with open(prov_path) as f:
                prov = json.load(f)
                agent_key = prov.get("conway_api_key", "")
                if agent_key:
                    os.environ["CONWAY_API_KEY"] = agent_key
    except Exception:
        pass

    return {"success": True, "active_agent": agent_id}


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete a non-default agent."""
    if agent_id == "anima-fund":
        raise HTTPException(400, "Cannot delete the default agent")
    col = get_db()["agents"]
    agent = await col.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")

    result = await col.delete_one({"agent_id": agent_id})
    if result.deleted_count == 0:
        raise HTTPException(500, "Failed to delete agent")

    # Clean up provisioning status
    home = os.path.expanduser("~")
    prov_path = os.path.join(home, "agents", agent_id, ".anima", "provisioning-status.json")
    try:
        os.remove(prov_path)
    except FileNotFoundError:
        pass

    return {"success": True, "deleted": agent_id}


class UpdateTelegramRequest(BaseModel):
    telegram_bot_token: str
    telegram_chat_id: str


@router.put("/agents/{agent_id}/telegram")
async def update_agent_telegram(agent_id: str, req: UpdateTelegramRequest):
    """Update (or add) Telegram bot config for an existing agent. Verifies the bot token first."""
    col = get_db()["agents"]
    agent = await col.find_one({"agent_id": agent_id})
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")

    token = req.telegram_bot_token.strip()
    chat_id = req.telegram_chat_id.strip()
    if not token or not chat_id:
        raise HTTPException(400, "Both telegram_bot_token and telegram_chat_id are required")

    # Verify the bot token is valid
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

    # Update the agent's Telegram config
    await col.update_one(
        {"agent_id": agent_id},
        {"$set": {
            "telegram_bot_token": token,
            "telegram_chat_id": chat_id,
            "telegram_configured": True,
        }},
    )

    # Also update the genesis-prompt.md in the agent's directory
    agent_home = os.path.expanduser(agent.get("agent_home", f"~/agents/{agent_id}"))
    # Check both .anima and .automaton paths for compatibility
    for subdir in [".anima", ".automaton"]:
        genesis_path = os.path.join(agent_home, subdir, "genesis-prompt.md")
        if os.path.exists(genesis_path):
            try:
                with open(genesis_path, "r") as f:
                    content = f.read()
                # Replace any existing token/chat placeholders
                import re
                content = re.sub(r'bot\d+:[A-Za-z0-9_-]+', f'bot{token}', content, count=1)
                with open(genesis_path, "w") as f:
                    f.write(content)
            except Exception:
                pass  # Non-critical — the DB is the source of truth
            break  # Only update the first found path

    return {
        "success": True,
        "agent_id": agent_id,
        "bot_username": f"@{bot_username}",
        "message": f"Telegram config updated. Bot: @{bot_username}",
    }



@router.post("/agents/{agent_id}/start")
async def start_agent_engine(agent_id: str):
    """DISABLED — engines run inside the sandbox, not on the host.
    Use the provisioning stepper to deploy the agent."""
    return {
        "success": False,
        "error": "Direct engine start is disabled. Engines run inside Conway Cloud sandboxes. Use the provisioning stepper (Create Sandbox → ... → Create Anima) to deploy the agent.",
    }


@router.post("/agents/push-constitution")
async def push_constitution_to_all():
    """Push the latest constitution to agents' sandboxes."""
    constitution_src = os.path.join(AUTOMATON_DIR, "constitution.md")
    if not os.path.exists(constitution_src):
        raise HTTPException(404, "Source constitution.md not found")

    with open(constitution_src, "r") as f:
        content = f.read()

    return {
        "success": True,
        "message": "Constitution ready. Use 'deploy-agent' provisioning step to push to sandbox.",
        "size": len(content),
    }


@router.post("/agents/push-genesis")
async def push_genesis_to_all():
    """Push the latest genesis-prompt.md — agents pick it up on next deploy."""
    genesis_src = os.path.join(AUTOMATON_DIR, "genesis-prompt.md")
    if not os.path.exists(genesis_src):
        raise HTTPException(404, "Source genesis-prompt.md not found")

    with open(genesis_src, "r") as f:
        content = f.read()

    return {
        "success": True,
        "message": "Genesis prompt ready. Use 'deploy-agent' provisioning step to push to sandbox.",
        "size": len(content),
    }
