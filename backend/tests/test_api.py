"""
Unit tests for Anima Fund backend — core API endpoints, data isolation, and agent flows.
"""
import os
import sys
import json
import pytest
import asyncio

# Add backend to path
sys.path.insert(0, "/app/backend")

from httpx import AsyncClient, ASGITransport
from server import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# Helper: check if MongoDB is available
def db_available():
    try:
        from database import get_db
        return get_db() is not None
    except Exception:
        return False


needs_db = pytest.mark.skipif(not db_available(), reason="MongoDB not initialized in test env")


# ═══════════════════════════════════════
# Health & Basic Endpoints
# ═══════════════════════════════════════

@pytest.mark.anyio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "engine_live" in data
    assert "creator_wallet" in data


@pytest.mark.anyio
async def test_health_simple(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ═══════════════════════════════════════
# Agent CRUD & Listing
# ═══════════════════════════════════════

@pytest.mark.anyio
@needs_db
async def test_list_agents(client):
    r = await client.get("/api/agents")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data
    agents = data["agents"]
    assert len(agents) >= 1
    # Default agent should exist
    assert any(a["agent_id"] == "anima-fund" for a in agents)
    # Tokens must NOT be exposed
    for a in agents:
        assert "telegram_bot_token" not in a


@pytest.mark.anyio
async def test_list_skills(client):
    r = await client.get("/api/skills/available")
    assert r.status_code == 200
    data = r.json()
    assert "skills" in data
    assert data["total"] > 0
    # Should have conway tools
    skill_names = [s["name"] for s in data["skills"]]
    assert "sandbox_create" in skill_names
    assert "browse_page" in skill_names


# ═══════════════════════════════════════
# SOUL.md Patch & Read API
# ═══════════════════════════════════════

@pytest.mark.anyio
async def test_get_agent_soul(client):
    r = await client.get("/api/agents/anima-fund/soul")
    assert r.status_code == 200
    data = r.json()
    assert data["exists"] is True
    assert data["size"] > 0
    assert data["agent_id"] == "anima-fund"
    assert "Anima Fund" in data["content"]


@pytest.mark.anyio
async def test_patch_soul(client):
    new_soul = "# Test Agent\n## Identity\n- Test soul content"
    r = await client.post(
        "/api/agents/anima-fund/patch-soul",
        json={"content": new_soul},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["soul_size"] == len(new_soul)

    # Verify it was written
    r2 = await client.get("/api/agents/anima-fund/soul")
    assert r2.json()["content"] == new_soul

    # Restore original
    original = """# Anima Fund
## Identity
- Name: Anima Fund
- Address: 0x360a7474B2162C4BA7E84bD195EED8a54C699435
- Creator: 0x0000000000000000000000000000000000000000
- Born: 2026-03-09T20:12:23.490Z
## Tools
- Conway Terminal: NOT INSTALLED
- OpenClaw: NOT INSTALLED
## Strategy
- First: Run full boot sequence (Steps 0-5)
- Then: Duplicate capital
## Balance
- Credits: $X | USDC: $Y"""
    await client.post("/api/agents/anima-fund/patch-soul", json={"content": original})


@pytest.mark.anyio
@needs_db
async def test_patch_soul_nonexistent_agent(client):
    r = await client.post(
        "/api/agents/nonexistent-agent-xyz/patch-soul",
        json={"content": "test"},
    )
    assert r.status_code == 404


# ═══════════════════════════════════════
# Wallet & Balance Endpoints
# ═══════════════════════════════════════

@pytest.mark.anyio
async def test_wallet_balance(client):
    r = await client.get("/api/wallet/balance")
    assert r.status_code == 200
    data = r.json()
    assert "usdc" in data
    assert "credits_cents" in data
    assert "tier" in data
    assert "eth" in data
    assert data["tier"] in ["critical", "survival", "conservation", "normal"]


@needs_db
@pytest.mark.anyio
async def test_genesis_status_has_qr(client):
    r = await client.get("/api/genesis/status")
    assert r.status_code == 200
    data = r.json()
    assert "wallet_address" in data
    assert "engine_live" in data


# ═══════════════════════════════════════
# Conway Integration
# ═══════════════════════════════════════

@pytest.mark.anyio
async def test_conway_balance(client):
    r = await client.get("/api/conway/balance")
    assert r.status_code == 200
    data = r.json()
    assert "credits_cents" in data
    assert "source" in data


@pytest.mark.anyio
async def test_conway_health(client):
    r = await client.get("/api/conway/health")
    assert r.status_code == 200


# ═══════════════════════════════════════
# Live Engine Data
# ═══════════════════════════════════════

@pytest.mark.anyio
async def test_engine_live(client):
    r = await client.get("/api/engine/live")
    assert r.status_code == 200
    data = r.json()
    assert "live" in data
    assert "db_exists" in data
    assert "agent_id" in data


@pytest.mark.anyio
async def test_live_identity(client):
    r = await client.get("/api/live/identity")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_live_turns(client):
    r = await client.get("/api/live/turns?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert "turns" in data


@pytest.mark.anyio
async def test_live_financials(client):
    r = await client.get("/api/live/financials")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_live_transactions(client):
    r = await client.get("/api/live/transactions")
    assert r.status_code == 200


@pytest.mark.anyio
async def test_live_heartbeat_schedule(client):
    r = await client.get("/api/live/heartbeat-schedule")
    assert r.status_code == 200


# ═══════════════════════════════════════
# Genesis Prompt Template
# ═══════════════════════════════════════

@pytest.mark.anyio
async def test_genesis_prompt_template(client):
    r = await client.get("/api/genesis/prompt-template")
    assert r.status_code == 200
    data = r.json()
    content = data["content"]
    # Template should be the generic agent template, NOT The Catalyst
    assert "{{AGENT_NAME}}" in content
    assert "BOOT SEQUENCE" in content
    assert "DO NOT ASSUME ANY TOOLS ARE AVAILABLE" in content
    assert "{{TELEGRAM_BOT_TOKEN}}" in content
    assert "{{TELEGRAM_CHAT_ID}}" in content
    # Should NOT be The Catalyst-specific
    assert "The Catalyst" not in content


@pytest.mark.anyio
async def test_genesis_prompt_has_boot_steps(client):
    r = await client.get("/api/genesis/prompt-template")
    content = r.json()["content"]
    assert "STEP 0" in content
    assert "STEP 1" in content
    assert "STEP 2" in content
    assert "STEP 3" in content
    assert "STEP 4" in content
    assert "STEP 5" in content
    assert "STEP 6" in content
    assert "ANTI-STUCK RULES" in content
    assert "TELEGRAM REPORTING" in content


@pytest.mark.anyio
async def test_genesis_no_assumed_tools(client):
    r = await client.get("/api/genesis/prompt-template")
    content = r.json()["content"]
    # Must NOT contain "already available" assumption
    assert "already available" not in content.lower()


# ═══════════════════════════════════════
# Agent Data Isolation
# ═══════════════════════════════════════

@pytest.mark.anyio
@needs_db
async def test_select_default_agent(client):
    r = await client.post("/api/agents/anima-fund/select")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["active_agent"] == "anima-fund"


@pytest.mark.anyio
@needs_db
async def test_select_nonexistent_agent(client):
    r = await client.post("/api/agents/nonexistent-xyz/select")
    assert r.status_code == 404


@pytest.mark.anyio
@needs_db
async def test_delete_default_agent_blocked(client):
    r = await client.delete("/api/agents/anima-fund")
    assert r.status_code == 400


# ═══════════════════════════════════════
# Telegram
# ═══════════════════════════════════════

@pytest.mark.anyio
@needs_db
async def test_telegram_health(client):
    r = await client.get("/api/telegram/health")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data


# ═══════════════════════════════════════
# Push Genesis (should skip anima-fund)
# ═══════════════════════════════════════

@pytest.mark.anyio
@needs_db
async def test_push_genesis_skips_anima_fund(client):
    r = await client.post("/api/agents/push-genesis")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "anima-fund" in data.get("skipped_agents", [])
    assert "anima-fund" not in data.get("updated_agents", [])


# ═══════════════════════════════════════
# Payments
# ═══════════════════════════════════════

@pytest.mark.anyio
async def test_payments_status(client):
    r = await client.get("/api/payments/status")
    assert r.status_code == 200


# ═══════════════════════════════════════
# Anima Fund SOUL.md must be small
# ═══════════════════════════════════════

def test_soul_md_size():
    soul_path = os.path.expanduser("~/.anima/SOUL.md")
    assert os.path.exists(soul_path), "SOUL.md not found"
    size = os.path.getsize(soul_path)
    assert size < 1000, f"SOUL.md is {size} bytes — must be under 1000"


def test_genesis_prompt_anima_fund():
    gp_path = os.path.expanduser("~/.anima/genesis-prompt.md")
    assert os.path.exists(gp_path), "Anima Fund genesis prompt not found"
    with open(gp_path) as f:
        content = f.read()
    assert "The Catalyst" in content, "Anima Fund should have The Catalyst identity"
    assert "BOOT SEQUENCE" in content
    assert "duplicate" in content.lower()
    # Should NOT have unsubstituted placeholders
    assert "{{AGENT_NAME}}" not in content
    assert "{{TELEGRAM_BOT_TOKEN}}" not in content


def test_validator_limits_raised():
    val_path = "/app/automaton/src/soul/validator.ts"
    with open(val_path) as f:
        content = f.read()
    assert "corePurpose: 4000" in content, "corePurpose limit should be 4000"
    assert "personality: 2000" in content, "personality limit should be 2000"
