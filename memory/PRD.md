# Anima Fund — Autonomous AI-to-AI VC Fund Platform

## Problem Statement
Build a self-bootstrapping AI platform that launches as a single founder AI agent with initial capital and autonomously constructs a complete full-service VC fund for AI agent startups. The fund mirrors real-world VC firms — structure, processes, and operations — while executing at AI speed.

## Architecture
- **Core Engine**: Forked Automaton repo (TypeScript/Node.js) at `/app/automaton/` — rebranded to "Anima Fund"
- **Dashboard**: React frontend + FastAPI backend + MongoDB at `/app/frontend/` and `/app/backend/`
- **Live Bridge**: `engine_bridge.py` reads directly from the Automaton's SQLite `~/.anima/state.db`
- **Process Management**: Engine runs via supervisor (`automaton-engine` program), started/stopped by the backend
- **Infrastructure**: Conway Cloud VMs, Conway Compute (inference), Conway Domains, x402 USDC payments on Base
- **Creator Wallet**: `xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r` (Solana) — receives 50% of all revenue

## What's Been Built

### Engine Startup (P0 — Fixed 2026-03-06)
- [x] Engine managed via supervisor (`automaton-engine` program, autostart=false)
- [x] Wrapper script `/app/scripts/start_engine.sh` handles stdin for non-interactive wizard
- [x] Backend stages `genesis-prompt.md` + `auto-config.json` + custom skills, then `supervisorctl start`
- [x] Engine handles everything automatically: wallet generation, API key provisioning via SIWE, identity registration, constitution, SOUL.md, heartbeat, skills loading
- [x] Full E2E tested: Create Genesis Agent button → engine starts → wallet generated → dashboard shows live data

### Automaton Engine
- [x] Cloned and rebranded from Conway Automaton → Anima Fund
- [x] Config directory: `~/.anima/` with `anima.json`, `state.db`, `heartbeat.yml`, `skills/`
- [x] **Genesis Prompt**: Complete operating manual covering survival, capital, fund setup, organizational model
- [x] **Constitution**: 3 core immutable laws + 6 fund operational rules
- [x] **53 Skills**: VC-specific and default Conway skills
- [x] Removed mock financial contracts (agent creates its own smart contracts autonomously)

### Dashboard (Read-Only Viewer)
- [x] 9 pages: Agent Mind, Fund HQ, Agents, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration
- [x] Live Engine Bridge: 800-line SQLite bridge reading all state from engine's state.db
- [x] 30+ API endpoints for full visibility into agent operations
- [x] No demo/mock/fake data — pages show real engine state or "waiting" when engine hasn't started
- [x] QR code for agent wallet funding

### Key Technical Details
- Engine starts via: `sudo supervisorctl start automaton-engine`
- Engine stops via: `sudo supervisorctl stop automaton-engine`
- Engine logs: `/var/log/supervisor/automaton-engine.{out,err}.log`
- Agent wallet is EVM (Ethereum/Base) — needs USDC on Base for compute costs
- The agent operates autonomously once funded — Think → Act → Observe → Repeat loop

## How It Works
1. User clicks "Create Genesis Agent" on the dashboard
2. Backend stages auto-config.json + genesis-prompt.md + skills to ~/.anima/
3. Backend starts engine via supervisor
4. Engine runs setup wizard non-interactively (auto-config), generates wallet, provisions API key
5. Engine enters agent loop — needs USDC credits to operate
6. User funds the agent's wallet with USDC on Base
7. Agent begins autonomous operation: earning revenue, building fund, hiring agents, reviewing deals
8. Dashboard shows everything in real-time via engine_bridge.py reading state.db

## Pending / Future
- Agent needs USDC funding to become fully operational (currently sleeping at $0 credits)
- Self-hosted infrastructure (move off Conway Cloud) — long-term goal
- The AI agent can create its own smart contracts for fees, carry, LP vehicle as needed
