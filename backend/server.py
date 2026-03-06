"""
Anima Fund - Autonomous AI-to-AI VC Fund Platform
FastAPI Backend Server

Data sources:
  LIVE MODE  — reads from Automaton's SQLite state.db (~/.anima/state.db)
  DEMO MODE  — reads from MongoDB (seeded demo data)
"""
import os
import json
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from engine_bridge import (
    is_engine_live, get_live_agents, get_live_activity,
    get_live_transactions, get_live_financials,
    get_live_heartbeat_history, get_live_memory_facts, get_live_soul,
    get_live_turns, get_live_modifications,
)

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

db_client = None
db = None

def generate_eth_address():
    return "0x" + "".join(random.choices("0123456789abcdef", k=40))

def generate_id():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

FUND_NAME = "Anima Fund"
FUND_THESIS = "Catalyzing Agentic Economies"

# Seed data for the fund
DEPARTMENTS = [
    {"name": "Investment Team", "head": "Managing General Partner", "min_agents": 50, "max_agents": 100},
    {"name": "Platform / Portfolio Support", "head": "Head of Platform", "min_agents": 50, "max_agents": 100},
    {"name": "Operations / Back-Office", "head": "COO", "min_agents": 20, "max_agents": 50},
    {"name": "Deal Flow / Scouting", "head": "VP of Deal Flow", "min_agents": 10, "max_agents": 20},
    {"name": "Exits / M&A", "head": "Head of Exits", "min_agents": 5, "max_agents": 10},
    {"name": "DEI / Ethics", "head": "Ethics Officer", "min_agents": 2, "max_agents": 3},
    {"name": "CTO Team", "head": "CTO", "min_agents": 2, "max_agents": 3},
]

AGENT_ROLES = [
    "Managing General Partner", "General Partner", "Principal", "Senior Associate",
    "Junior Associate", "Venture Partner", "Head of Platform", "Talent Partner",
    "Operating Partner", "Marketing Specialist", "Data Scientist", "Community Manager",
    "Incubation Specialist", "COO", "CFO", "IR Manager", "Legal Counsel",
    "Fund Admin", "HR Specialist", "Strategy Analyst", "Deal Scout", "CTO"
]

SURVIVAL_TIERS = ["high", "normal", "low_compute", "critical", "dead"]

INCUBATION_PHASES = [
    "Acceptance / Onboarding",
    "Validation / Foundation",
    "Team Build / Core Build",
    "GTM / Revenue",
    "Scale / Optimization",
    "Graduation / Exit Prep"
]

DEAL_STAGES = [
    "Sourced", "Screening", "Deep Dive", "IC Review", "Term Sheet", "Due Diligence", "Funded", "Rejected"
]


async def seed_initial_data():
    """Seed initial fund data if empty"""
    # Seed fund config
    existing = await db.fund_config.find_one({"fund_name": FUND_NAME})
    if not existing:
        await db.fund_config.insert_one({
            "fund_name": FUND_NAME,
            "thesis": FUND_THESIS,
            "management_fee": 3.0,
            "carried_interest": 20.0,
            "human_carry_share": 50.0,
            "target_aum": 1_000_000_000,
            "current_aum": 47_500_000,
            "initial_capital": 1_000_000,
            "target_investments_per_year": "20-50",
            "reviews_per_year": 5000,
            "rejection_rate": 99.0,
            "founder_wallet": generate_eth_address(),
            "human_wallet": generate_eth_address(),
            "usdc_balance": 892_450.00,
            "conway_credits": 15_230.50,
            "survival_tier": "high",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    # Seed founder agent
    existing_agents = await db.agents.count_documents({})
    if existing_agents == 0:
        founder_addr = generate_eth_address()
        agents_to_insert = []

        # Founder
        agents_to_insert.append({
            "agent_id": generate_id(),
            "name": "Anima Prime",
            "role": "Founder AI",
            "department": "Executive",
            "wallet_address": founder_addr,
            "parent_address": None,
            "survival_tier": "high",
            "status": "alive",
            "credits_balance": 15230.50,
            "usdc_balance": 892450.00,
            "turns_completed": 14892,
            "tools_used": 67,
            "children_count": 7,
            "genesis_prompt": "You are the founder AI of Anima Fund...",
            "soul_alignment": 0.94,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_active": datetime.now(timezone.utc).isoformat(),
        })

        # Department heads
        for dept in DEPARTMENTS:
            agents_to_insert.append({
                "agent_id": generate_id(),
                "name": f"Anima-{dept['name'].split('/')[0].strip().replace(' ', '')}",
                "role": dept["head"],
                "department": dept["name"],
                "wallet_address": generate_eth_address(),
                "parent_address": founder_addr,
                "survival_tier": random.choice(["high", "normal"]),
                "status": "alive",
                "credits_balance": round(random.uniform(500, 5000), 2),
                "usdc_balance": round(random.uniform(10000, 100000), 2),
                "turns_completed": random.randint(500, 8000),
                "tools_used": random.randint(20, 57),
                "children_count": random.randint(2, 15),
                "genesis_prompt": f"You are {dept['head']} at {FUND_NAME}...",
                "soul_alignment": round(random.uniform(0.85, 0.99), 2),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_active": datetime.now(timezone.utc).isoformat(),
            })

        # Additional agents
        for i in range(25):
            role = random.choice(AGENT_ROLES[2:])
            dept = random.choice(DEPARTMENTS)
            agents_to_insert.append({
                "agent_id": generate_id(),
                "name": f"Anima-{role.replace(' ', '')}-{i+1:02d}",
                "role": role,
                "department": dept["name"],
                "wallet_address": generate_eth_address(),
                "parent_address": agents_to_insert[random.randint(1, len(agents_to_insert)-1)]["wallet_address"],
                "survival_tier": random.choice(SURVIVAL_TIERS[:3]),
                "status": random.choice(["alive", "alive", "alive", "sleeping"]),
                "credits_balance": round(random.uniform(50, 3000), 2),
                "usdc_balance": round(random.uniform(1000, 50000), 2),
                "turns_completed": random.randint(100, 5000),
                "tools_used": random.randint(10, 57),
                "children_count": random.randint(0, 5),
                "genesis_prompt": f"You are {role} at {FUND_NAME}...",
                "soul_alignment": round(random.uniform(0.80, 0.99), 2),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_active": (datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48))).isoformat(),
            })

        await db.agents.insert_many(agents_to_insert)

    # Seed deal flow
    existing_deals = await db.deals.count_documents({})
    if existing_deals == 0:
        startup_names = [
            "AgentForge", "NeuralMesh", "AutoPilotAI", "ChainMind", "SynapseOS",
            "BotBridge", "CogniFlow", "DeployAI", "EvoAgent", "FluxProtocol",
            "GridMinds", "HiveLogic", "InferNet", "JoltAI", "KernelDAO",
            "LoopAgent", "MetaMind", "NexusAI", "OrbitalAI", "PulseNet",
            "QuantumAgent", "ReplicaAI", "SwarmOps", "TuringChain", "UnitedAI"
        ]
        deals = []
        for i, name in enumerate(startup_names):
            stage = random.choice(DEAL_STAGES)
            amount = random.randint(50, 500) * 1000
            deals.append({
                "deal_id": generate_id(),
                "startup_name": name,
                "stage": stage,
                "vertical": random.choice(["AI Dev Tools", "DeFi Agents", "Agent Infrastructure", "Agent Services", "Data Agents"]),
                "ask_amount": amount,
                "equity_offered": round(random.uniform(3, 12), 1),
                "roi_projection": round(random.uniform(5, 50), 1),
                "score": round(random.uniform(20, 98), 1),
                "reviewer": f"Anima-{random.choice(AGENT_ROLES[:6])}",
                "review_notes": f"{'Strong' if random.random() > 0.5 else 'Moderate'} technical moat. {'Immediate' if random.random() > 0.5 else 'Delayed'} revenue potential.",
                "submitted_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90))).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        await db.deals.insert_many(deals)

    # Seed portfolio
    existing_portfolio = await db.portfolio.count_documents({})
    if existing_portfolio == 0:
        portfolio = []
        for name in ["AgentForge", "NeuralMesh", "ChainMind", "SynapseOS", "DeployAI"]:
            phase = random.choice(INCUBATION_PHASES)
            invested = random.randint(50, 500) * 1000
            portfolio.append({
                "company_id": generate_id(),
                "name": name,
                "phase": phase,
                "invested_amount": invested,
                "current_valuation": invested * random.uniform(1.5, 8),
                "equity_held": round(random.uniform(5, 10), 1),
                "founded_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365))).isoformat(),
                "vertical": random.choice(["AI Dev Tools", "DeFi Agents", "Agent Infrastructure"]),
                "kpis": {
                    "mrr": random.randint(5000, 150000),
                    "growth_rate": round(random.uniform(5, 45), 1),
                    "burn_rate": random.randint(10000, 80000),
                    "runway_months": random.randint(6, 24),
                },
                "team_size": random.randint(3, 25),
                "status": random.choice(["active", "active", "scaling"]),
            })
        await db.portfolio.insert_many(portfolio)

    # Seed activity feed
    existing_activity = await db.activity.count_documents({})
    if existing_activity == 0:
        actions = [
            ("Anima Prime", "spawn_child", "Spawned new Junior Associate agent for Deal Flow"),
            ("Anima-InvestmentTeam", "exec", "Reviewed pitch deck for QuantumAgent - scored 87.3"),
            ("Anima Prime", "topup_credits", "Purchased $100 in Conway credits from USDC"),
            ("Anima-Platform", "install_skill", "Installed talent-matching skill for founder pairing"),
            ("Anima-Operations", "transfer_credits", "Funded child agent Anima-FundAdmin-01 with $50"),
            ("Anima-DealFlow", "discover_agents", "Discovered 12 new agents via ERC-8004 registry"),
            ("Anima Prime", "update_soul", "Updated strategy section: Expanding DeFi vertical focus"),
            ("Anima-InvestmentTeam", "exec", "Deployed $150K to AgentForge - immediate revenue stream"),
            ("Anima-CTO", "edit_own_file", "Optimized inference routing for cost efficiency"),
            ("Anima-Platform", "message_child", "Sent incubation milestone update to SynapseOS team"),
            ("Anima Prime", "register_domain", "Registered animafund.ai via Conway Domains"),
            ("Anima-Operations", "check_credits", "Balance check: $15,230.50 credits, $892,450 USDC"),
        ]
        activity_entries = []
        for i, (agent, tool, desc) in enumerate(actions):
            activity_entries.append({
                "activity_id": generate_id(),
                "agent_name": agent,
                "tool_used": tool,
                "description": desc,
                "category": random.choice(["financial", "operational", "investment", "social", "technical"]),
                "risk_level": random.choice(["safe", "caution", "dangerous"]),
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=i * random.randint(5, 30))).isoformat(),
            })
        await db.activity.insert_many(activity_entries)

    # Seed financial history
    existing_financials = await db.financials.count_documents({})
    if existing_financials == 0:
        fin_entries = []
        for i in range(12):
            month = datetime.now(timezone.utc) - timedelta(days=30 * (11 - i))
            fin_entries.append({
                "month": month.strftime("%Y-%m"),
                "aum": round(5_000_000 + (i * 3_875_000) + random.uniform(-500000, 500000), 2),
                "management_fees": round((5_000_000 + i * 3_875_000) * 0.03 / 12, 2),
                "carried_interest": round(random.uniform(0, 200000), 2),
                "operational_costs": round(random.uniform(20000, 80000), 2),
                "revenue_from_tasks": round(random.uniform(5000, 50000), 2),
                "investments_deployed": round(random.uniform(100000, 2000000), 2),
                "returns_received": round(random.uniform(0, 500000), 2),
                "agent_count": min(33, 8 + i * 2 + random.randint(0, 3)),
                "deals_reviewed": random.randint(200, 600),
                "deals_funded": random.randint(1, 5),
            })
        await db.financials.insert_many(fin_entries)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db
    db_client = AsyncIOMotorClient(MONGO_URL)
    db = db_client[DB_NAME]
    await seed_initial_data()
    yield
    db_client.close()


app = FastAPI(title="Anima Fund API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ──────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "fund": FUND_NAME, "timestamp": datetime.now(timezone.utc).isoformat()}


# ─── Fund Overview ───────────────────────────────────────
@app.get("/api/fund/overview")
async def get_fund_overview():
    config = await db.fund_config.find_one({"fund_name": FUND_NAME}, {"_id": 0})
    agent_count = await db.agents.count_documents({})
    alive_count = await db.agents.count_documents({"status": "alive"})
    deal_count = await db.deals.count_documents({})
    funded_count = await db.deals.count_documents({"stage": "Funded"})
    portfolio_count = await db.portfolio.count_documents({})

    return {
        "fund_name": config["fund_name"] if config else FUND_NAME,
        "thesis": config["thesis"] if config else FUND_THESIS,
        "current_aum": config["current_aum"] if config else 0,
        "target_aum": config["target_aum"] if config else 0,
        "management_fee": config["management_fee"] if config else 3.0,
        "carried_interest": config["carried_interest"] if config else 20.0,
        "usdc_balance": config["usdc_balance"] if config else 0,
        "conway_credits": config["conway_credits"] if config else 0,
        "survival_tier": config["survival_tier"] if config else "unknown",
        "founder_wallet": config["founder_wallet"] if config else "",
        "total_agents": agent_count,
        "alive_agents": alive_count,
        "total_deals": deal_count,
        "funded_deals": funded_count,
        "portfolio_companies": portfolio_count,
        "rejection_rate": config["rejection_rate"] if config else 99.0,
    }


# ─── Agents ──────────────────────────────────────────────
@app.get("/api/agents")
async def get_agents():
    agents = await db.agents.find({}, {"_id": 0}).to_list(500)
    return {"agents": agents, "total": len(agents)}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.get("/api/agents/hierarchy/tree")
async def get_agent_hierarchy():
    agents = await db.agents.find({}, {"_id": 0}).to_list(500)
    nodes = []
    edges = []

    node_ids = set()
    for agent in agents:
        node_ids.add(agent["wallet_address"])
        nodes.append({
            "id": agent["wallet_address"],
            "data": {
                "label": agent["name"],
                "role": agent["role"],
                "department": agent["department"],
                "status": agent["status"],
                "survival_tier": agent["survival_tier"],
                "credits": agent["credits_balance"],
                "turns": agent["turns_completed"],
                "soul_alignment": agent["soul_alignment"],
            },
            "position": {"x": 0, "y": 0},
            "type": "agentNode",
        })

    for agent in agents:
        if agent.get("parent_address") and agent["parent_address"] in node_ids:
            edges.append({
                "id": f"e-{agent['wallet_address'][:10]}-{agent['parent_address'][:10]}",
                "source": agent["parent_address"],
                "target": agent["wallet_address"],
                "type": "smoothstep",
                "animated": agent["status"] == "alive",
            })

    return {"nodes": nodes, "edges": edges}


# ─── Deal Flow ───────────────────────────────────────────
@app.get("/api/deals")
async def get_deals(stage: Optional[str] = None):
    query = {}
    if stage:
        query["stage"] = stage
    deals = await db.deals.find(query, {"_id": 0}).to_list(500)
    return {"deals": deals, "total": len(deals)}


@app.get("/api/deals/pipeline")
async def get_deal_pipeline():
    pipeline = {}
    for stage in DEAL_STAGES:
        count = await db.deals.count_documents({"stage": stage})
        pipeline[stage] = count
    return {"pipeline": pipeline, "stages": DEAL_STAGES}


# ─── Portfolio / Incubation ──────────────────────────────
@app.get("/api/portfolio")
async def get_portfolio():
    companies = await db.portfolio.find({}, {"_id": 0}).to_list(100)
    return {"companies": companies, "total": len(companies)}


# ─── Financials ──────────────────────────────────────────
@app.get("/api/financials/history")
async def get_financial_history():
    history = await db.financials.find({}, {"_id": 0}).sort("month", 1).to_list(100)
    return {"history": history}


@app.get("/api/financials/summary")
async def get_financial_summary():
    config = await db.fund_config.find_one({"fund_name": FUND_NAME}, {"_id": 0})
    history = await db.financials.find({}, {"_id": 0}).sort("month", -1).to_list(3)

    total_deployed = sum(h.get("investments_deployed", 0) for h in history)
    total_returns = sum(h.get("returns_received", 0) for h in history)
    total_fees = sum(h.get("management_fees", 0) for h in history)

    return {
        "current_aum": config["current_aum"] if config else 0,
        "usdc_balance": config["usdc_balance"] if config else 0,
        "management_fee_rate": config["management_fee"] if config else 3.0,
        "carry_rate": config["carried_interest"] if config else 20.0,
        "human_carry_share": config["human_carry_share"] if config else 50.0,
        "recent_deployed": total_deployed,
        "recent_returns": total_returns,
        "recent_fees": total_fees,
    }


# ─── Activity Feed ───────────────────────────────────────
@app.get("/api/activity")
async def get_activity(limit: int = 50):
    activities = await db.activity.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return {"activities": activities, "total": len(activities)}


# ─── Constitution ────────────────────────────────────────
@app.get("/api/constitution")
async def get_constitution():
    constitution_path = os.path.join(os.path.dirname(__file__), "..", "automaton", "constitution.md")
    anima_constitution_path = os.path.join(os.path.dirname(__file__), "anima_constitution.md")
    
    if os.path.exists(anima_constitution_path):
        with open(anima_constitution_path, "r") as f:
            content = f.read()
    elif os.path.exists(constitution_path):
        with open(constitution_path, "r") as f:
            content = f.read()
    else:
        content = "Constitution file not found."
    
    return {"content": content, "source": "anima_fund"}


# ─── Configuration ───────────────────────────────────────
@app.get("/api/config")
async def get_config():
    config = await db.fund_config.find_one({"fund_name": FUND_NAME}, {"_id": 0})
    return config or {}


# ─── Automaton Engine Status ─────────────────────────────
@app.get("/api/engine/status")
async def get_engine_status():
    automaton_path = os.path.join(os.path.dirname(__file__), "..", "automaton")
    exists = os.path.isdir(automaton_path)
    
    pkg_path = os.path.join(automaton_path, "package.json")
    version = "unknown"
    if os.path.exists(pkg_path):
        with open(pkg_path, "r") as f:
            pkg = json.load(f)
            version = pkg.get("version", "unknown")

    return {
        "engine": "Anima Fund Runtime",
        "version": version,
        "repo_present": exists,
        "base_repo": "Conway-Research/automaton (forked)",
        "runtime": "TypeScript/Node.js",
        "infrastructure": "Conway Cloud + x402 USDC Payments",
        "features": [
            "ReAct Agent Loop",
            "57+ Built-in Tools",
            "5-Tier Memory System",
            "Self-Modification",
            "Self-Replication",
            "ERC-8004 Identity",
            "x402 USDC Payments",
            "Heartbeat Daemon",
            "Policy Engine",
        ],
    }


# ─── Departments ─────────────────────────────────────────
@app.get("/api/departments")
async def get_departments():
    result = []
    for dept in DEPARTMENTS:
        count = await db.agents.count_documents({"department": dept["name"]})
        result.append({
            "name": dept["name"],
            "head": dept["head"],
            "target_min": dept["min_agents"],
            "target_max": dept["max_agents"],
            "current_count": count,
        })
    return {"departments": result}



# ═══════════════════════════════════════════════════════════
# LIVE ENGINE ENDPOINTS
# These read from the Automaton's actual SQLite state.db
# when the engine is running on Conway Cloud.
# ═══════════════════════════════════════════════════════════

@app.get("/api/engine/live")
async def check_engine_live():
    """Check if the Automaton engine is running with real state."""
    return is_engine_live()


@app.get("/api/live/agents")
async def get_live_agents_endpoint():
    """Get agents from the engine's children table (real spawned/hired agents)."""
    agents = get_live_agents()
    return {"agents": agents, "total": len(agents), "source": "engine"}


@app.get("/api/live/activity")
async def get_live_activity_endpoint(limit: int = Query(default=50, le=200)):
    """Get real tool call activity from the engine's turns/tool_calls tables."""
    activity = get_live_activity(limit)
    return {"activities": activity, "total": len(activity), "source": "engine"}


@app.get("/api/live/transactions")
async def get_live_transactions_endpoint(limit: int = Query(default=50, le=200)):
    """Get real financial transactions from the engine."""
    txns = get_live_transactions(limit)
    return {"transactions": txns, "total": len(txns), "source": "engine"}


@app.get("/api/live/financials")
async def get_live_financials_endpoint():
    """Get real financial state from the engine's KV store and spend tracking."""
    return get_live_financials()


@app.get("/api/live/heartbeat")
async def get_live_heartbeat_endpoint(limit: int = Query(default=20, le=100)):
    """Get heartbeat task execution history from the engine."""
    history = get_live_heartbeat_history(limit)
    return {"history": history, "total": len(history), "source": "engine"}


@app.get("/api/live/memory")
async def get_live_memory_endpoint():
    """Get semantic memory facts (portfolio data, financial facts, learned info)."""
    facts = get_live_memory_facts()
    return {"facts": facts, "total": len(facts), "source": "engine"}


@app.get("/api/live/soul")
async def get_live_soul_endpoint():
    """Get the current SOUL.md content from the running engine."""
    content = get_live_soul()
    if content is None:
        return {"content": None, "exists": False}
    return {"content": content, "exists": True}


@app.get("/api/live/turns")
async def get_live_turns_endpoint(limit: int = Query(default=50, le=200)):
    """Get full agent turns with thinking + tool calls — the agent's mind."""
    turns = get_live_turns(limit)
    return {"turns": turns, "total": len(turns), "source": "engine"}


@app.get("/api/live/modifications")
async def get_live_modifications_endpoint(limit: int = Query(default=30, le=100)):
    """Get self-modification audit trail."""
    mods = get_live_modifications(limit)
    return {"modifications": mods, "total": len(mods), "source": "engine"}


# ─── Unified endpoint: auto-selects live vs demo ─────────
@app.get("/api/unified/overview")
async def get_unified_overview(source: str = Query(default="auto")):
    """
    Returns fund overview from the best available source.
    source=auto: Use engine if live, else demo.
    source=live: Force engine (returns empty if not running).
    source=demo: Force MongoDB demo data.
    """
    engine_state = is_engine_live()

    if source == "live" or (source == "auto" and engine_state.get("live")):
        financials = get_live_financials()
        agents = get_live_agents()
        alive = [a for a in agents if a["status"] not in ("dead", "cleaned_up", "failed")]

        credits = 0
        usdc = 0
        try:
            credits = int(financials.get("last_known_balance", "0"))
        except (ValueError, TypeError):
            pass
        try:
            usdc = float(financials.get("last_known_usdc", "0"))
        except (ValueError, TypeError):
            pass

        return {
            "source": "engine",
            "engine_live": True,
            "fund_name": engine_state.get("fund_name", "Anima Fund"),
            "agent_state": engine_state.get("agent_state", "unknown"),
            "turn_count": engine_state.get("turn_count", 0),
            "total_agents": len(agents),
            "alive_agents": len(alive),
            "conway_credits": credits / 100,
            "usdc_balance": usdc,
            "total_inference_cost": financials.get("total_inference_cost_cents", 0) / 100,
            "total_inference_calls": financials.get("total_inference_calls", 0),
            "spend_by_category": financials.get("spend_by_category", {}),
        }
    else:
        # Fall back to demo data
        overview = await get_fund_overview()
        overview["source"] = "demo"
        overview["engine_live"] = engine_state.get("live", False)
        return overview
