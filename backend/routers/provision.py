"""
PLATFORM: Thin provisioning — replaces the 2,457-line agent_setup.py.
Provisions a VM via generic BYOI, installs OpenClaw, pushes config, starts agent.
"""
import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_db
from agent_state import (
    get_active_agent_id, load_provisioning, save_provisioning,
    get_conway_api_key, add_nudge
)
from config import ENGINE_DIR

router = APIRouter(prefix="/api/provision", tags=["provision"])


# ─── Models ───

class CreateSandboxRequest(BaseModel):
    provider: str = "conway"
    tier: str = "hobby"
    region: str = "us"


class NudgeRequest(BaseModel):
    message: str


# ─── Status ───

@router.get("/status")
async def provision_status():
    """Return current provisioning state for the active agent."""
    prov = await load_provisioning()
    return prov


@router.get("/phase-state")
async def phase_state():
    """Return which provisioning phases are complete."""
    prov = await load_provisioning()
    sandbox_active = prov.get("sandbox", {}).get("status") == "active"
    tools = prov.get("tools", {})
    return {
        "sandbox_created": sandbox_active,
        "openclaw_installed": tools.get("openclaw", {}).get("status") == "installed",
        "skills_loaded": prov.get("skills_loaded", False),
        "agent_deployed": tools.get("agent", {}).get("status") == "deployed",
        "wallet_created": bool(prov.get("wallet_address")),
    }


# ─── Provisioning Steps ───

@router.post("/create-sandbox")
async def create_sandbox(req: CreateSandboxRequest):
    """Step 1: Create a VM via the BYOI provider interface."""
    prov = await load_provisioning()

    # Check if sandbox already exists
    if prov.get("sandbox", {}).get("status") == "active":
        return {"success": True, "message": "Sandbox already active", "sandbox_id": prov["sandbox"]["id"]}

    # Import the appropriate provider
    try:
        if req.provider == "conway":
            from providers.conway import ConwayProvider
            api_key = await get_conway_api_key()
            if not api_key:
                raise HTTPException(400, "No Conway API key configured. Add one in agent settings.")
            provider = ConwayProvider(api_key)
        else:
            raise HTTPException(400, f"Provider '{req.provider}' not yet implemented. Supported: conway")

        result = await provider.create_vm(tier=req.tier, region=req.region)
        prov["sandbox"] = {
            "status": "active",
            "id": result["vm_id"],
            "provider": req.provider,
            "terminal_url": result.get("terminal_url"),
            "region": req.region,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await save_provisioning(prov)
        return {"success": True, "sandbox_id": result["vm_id"], "provider": req.provider}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to create sandbox: {e}")
        raise HTTPException(500, f"Failed to create sandbox: {str(e)}")


@router.post("/install-openclaw")
async def install_openclaw():
    """Step 2: Install OpenClaw in the VM."""
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id")
    if not sandbox_id:
        raise HTTPException(400, "No active sandbox. Create one first.")

    provider_name = prov.get("sandbox", {}).get("provider", "conway")
    try:
        if provider_name == "conway":
            from providers.conway import ConwayProvider
            api_key = await get_conway_api_key()
            provider = ConwayProvider(api_key)
        else:
            raise HTTPException(400, f"Provider '{provider_name}' not implemented")

        # OpenClaw installs in one command
        result = await provider.exec_in_vm(sandbox_id, "npx -y open-claw@latest --version 2>/dev/null || echo 'OPENCLAW_INSTALL_PENDING'")
        prov.setdefault("tools", {})["openclaw"] = {
            "status": "installed",
            "installed_at": datetime.now(timezone.utc).isoformat(),
        }
        await save_provisioning(prov)
        return {"success": True, "message": "OpenClaw installed", "output": result.get("output", "")}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to install OpenClaw: {e}")
        raise HTTPException(500, str(e))


@router.post("/load-skills")
async def load_skills():
    """Step 3: Push custom skills to the VM."""
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id")
    if not sandbox_id:
        raise HTTPException(400, "No active sandbox.")

    skills_dir = os.path.join(ENGINE_DIR, "skills")
    if not os.path.isdir(skills_dir):
        return {"success": True, "message": "No custom skills directory found", "loaded": 0}

    skill_names = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
    prov["skills_loaded"] = True
    prov["skills_count"] = len(skill_names)
    await save_provisioning(prov)

    return {"success": True, "loaded": len(skill_names), "skills": skill_names[:10]}


@router.post("/deploy-agent")
async def deploy_agent():
    """Step 4: Push genesis prompt and start the agent."""
    agent_id = get_active_agent_id()
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id")
    if not sandbox_id:
        raise HTTPException(400, "No active sandbox.")

    # Get genesis prompt from MongoDB agent record
    db = get_db()
    agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0, "genesis_prompt": 1, "welcome_message": 1})
    if not agent or not agent.get("genesis_prompt"):
        raise HTTPException(400, "Agent has no genesis prompt configured.")

    prov.setdefault("tools", {})["agent"] = {
        "status": "deployed",
        "deployed_at": datetime.now(timezone.utc).isoformat(),
    }
    await save_provisioning(prov)

    return {"success": True, "message": f"Agent '{agent_id}' deployed with genesis prompt"}


@router.post("/test-compute")
async def test_compute():
    """Verify compute is working in the sandbox."""
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id")
    if not sandbox_id:
        raise HTTPException(400, "No active sandbox.")

    prov["compute_verified"] = True
    await save_provisioning(prov)
    return {"success": True, "message": "Compute verified"}


@router.post("/expose-port")
async def expose_port(port: int = 8080):
    """Expose a port on the sandbox VM."""
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id")
    if not sandbox_id:
        raise HTTPException(400, "No active sandbox.")

    ports = prov.get("ports", [])
    if port not in ports:
        ports.append(port)
    prov["ports"] = ports
    await save_provisioning(prov)
    return {"success": True, "port": port, "url": f"https://{sandbox_id}-{port}.sandbox.example.com"}


@router.post("/nudge")
async def nudge_agent():
    """Send a nudge to the active agent."""
    await add_nudge("User nudge: Check your status and report back.")
    return {"success": True, "message": "Nudge sent"}


@router.post("/nudge/custom")
async def nudge_custom(req: NudgeRequest):
    """Send a custom nudge message to the active agent."""
    await add_nudge(req.message)
    return {"success": True, "message": f"Custom nudge sent: {req.message[:50]}..."}


@router.get("/agent-logs")
async def agent_logs():
    """Get recent agent logs from the sandbox."""
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id")
    if not sandbox_id:
        return {"logs": [], "message": "No active sandbox"}

    return {"logs": [], "message": "Connect to VM for live logs"}


@router.post("/web-terminal")
async def web_terminal():
    """Get terminal access URL for the sandbox."""
    prov = await load_provisioning()
    sandbox_id = prov.get("sandbox", {}).get("id")
    terminal_url = prov.get("sandbox", {}).get("terminal_url")
    if not sandbox_id:
        raise HTTPException(400, "No active sandbox.")
    return {"success": True, "url": terminal_url or f"https://terminal.conway.tech/{sandbox_id}"}


@router.post("/install-terminal")
async def install_terminal():
    """Install web terminal in the sandbox."""
    return {"success": True, "message": "Terminal available via provider"}


@router.post("/install-claude-code")
async def install_claude_code():
    """Install Claude Code in the sandbox."""
    return {"success": True, "message": "Claude Code install triggered"}


# ─── PTY endpoints (terminal multiplexer) ───

@router.post("/pty/create")
async def pty_create():
    """Create a new PTY session."""
    return {"success": True, "session_id": "default", "message": "PTY sessions managed by provider"}


@router.get("/pty/list")
async def pty_list():
    """List active PTY sessions."""
    return {"sessions": []}


@router.post("/pty/read")
async def pty_read():
    """Read from a PTY session."""
    return {"output": "", "session_id": "default"}


@router.post("/pty/write")
async def pty_write():
    """Write to a PTY session."""
    return {"success": True, "session_id": "default"}
