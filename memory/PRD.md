# Anima Fund — Autonomous AI-to-AI VC Fund Platform

## Problem Statement
Build a self-bootstrapping AI platform that launches as a single founder AI agent with $1M USDC initial capital and autonomously constructs a complete full-service VC fund for AI agent startups. The fund mirrors real-world VC firms in every detail — structure, processes, and operations — while executing at AI speed.

## Architecture
- **Core Engine**: Forked Automaton repo (TypeScript/Node.js) at `/app/automaton/` — rebranded to "Anima Fund"
- **Dashboard**: React frontend + FastAPI backend + MongoDB at `/app/frontend/` and `/app/backend/`
- **Live Bridge**: `engine_bridge.py` reads directly from the Automaton's SQLite `~/.anima/state.db`
- **Infrastructure**: Conway Cloud VMs, Conway Compute (inference), Conway Domains, x402 USDC payments on Base and Solana
- **Creator Wallet**: `xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r` (Solana) — receives 50% of all revenue

## What's Been Built

### Automaton Engine Modifications
- [x] Cloned and rebranded from Conway Automaton → Anima Fund (18+ files)
- [x] Package: `@anima/fund-runtime`, CLI: `@anima/fund-cli`
- [x] Config directory: `~/.anima/` with `anima.json`, `state.db`, `heartbeat.yml`, `skills/`
- [x] Custom ASCII banner, system prompt identity, CLI help text
- [x] **Genesis Prompt** (255 lines): Complete operating manual covering survival, capital duplication, fund setup, organizational model (all departments, roles, agent counts, specialized DD sub-teams), hierarchy with escalation thresholds, deal flow (5K+ reviews, 99% rejection, 6-step parallel evaluation), incubation (6 phases with Capital Allocation Maps, milestone release, clawback), continuous operations, LP vehicle, full autonomy
- [x] **Constitution** (9 laws): 3 core immutable laws + 6 fund operational rules including Solana payout rule with creator wallet hardcoded
- [x] **5 VC Skills**: deal-evaluation, cost-validation, incubation-management, hiring-validation, capital-duplication
- [x] **Mock Financial Contracts**: FeeDistributor, LP Vehicle, Investment Vault, NAV calculator with Solidity patterns for production swap
- [x] **Deployment Script**: `deploy.sh` — builds, installs skills/constitution/genesis, displays pre-flight summary, starts founder AI
- [x] **Wizard Auto-Load**: Setup wizard reads genesis prompt from staged file automatically

### Dashboard (Visualization Only — Reads, Never Writes)
- [x] 9 pages: Overview, Fund HQ (Tycoon), Agent Mind, Agent Network, Deal Flow, Portfolio, Financials, Activity, Configuration
- [x] **Fund HQ**: Animated multi-floor office building — floors generated dynamically from actual agent data, no hardcoded structure
- [x] **Agent Mind**: Real-time view of agent consciousness with per-agent selector labeled by role. Thinking blocks, tool call expansion, search, filters
- [x] **Live Engine Bridge**: 550-line SQLite bridge reading from state.db (turns, tool_calls, children, transactions, heartbeat_history, spend_tracking, inference_costs, semantic_memory, relationship_memory, discovered_agents_cache, inbox_messages, child_lifecycle_events, soul_history)
- [x] **Demo/Live Toggle**: Demo reads MongoDB seed data. Live reads engine SQLite. Auto-switches when engine comes online.
- [x] 26 backend API endpoints including 10 live engine endpoints

### Creator Revenue
- [x] Solana wallet `xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r` embedded in genesis prompt (4x), constitution (1x), deploy script (2x)
- [x] 50% of ALL revenue (management fees, carried interest, deal flow income) → creator wallet via x402 on Solana

## Deployment Steps
1. Fund the agent's Base wallet with USDC (for Conway Cloud compute/inference)
2. Ensure Solana USDC available for creator payouts
3. `cd /app/automaton && ./deploy.sh`
4. The wizard runs → enter a name → genesis prompt auto-loads → agent starts
5. Open the dashboard to watch the fund build itself

## What Happens After Deployment
The founder AI reads the genesis prompt and begins executing autonomously:
1. Earns money to survive (consulting, services, domains, skills — whatever works)
2. Names the fund, creates website, registers on-chain
3. Hires agents — both spawned (internal) and discovered (external sovereign agents from across the internet)
4. Builds organizational structure (Investment Team, Platform, Operations, Deal Flow, etc.)
5. Begins reviewing deals (5K+/year, 99% rejection)
6. Funds AI startups ($50K-$500K, 5-10% equity)
7. Runs incubation (6 phases, real products, real revenue)
8. Sends 50% of all revenue to creator on Solana
9. Scales indefinitely — 1-2 agents per $50M AUM

The dashboard shows all of this in real-time. The AI decides everything.
