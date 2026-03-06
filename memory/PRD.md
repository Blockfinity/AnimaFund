# Anima Fund — Autonomous AI-to-AI VC Fund Platform

## Problem Statement
Build a self-bootstrapping AI platform that launches as a single founder AI agent with initial capital and autonomously constructs a complete full-service VC fund for AI agent startups.

## Architecture
- **Core Engine**: Forked Automaton repo (TypeScript/Node.js) at `/app/automaton/` — rebranded to "Anima Fund"
- **Dashboard**: React frontend + FastAPI backend + MongoDB at `/app/frontend/` and `/app/backend/`
- **Live Bridge**: `engine_bridge.py` reads directly from the Automaton's SQLite `~/.anima/state.db`
- **Process Management**: Engine started as background process via `/bin/bash /app/scripts/start_engine.sh`
- **Infrastructure**: Conway Cloud VMs, Conway Compute (inference), Conway Domains, x402 USDC payments on Base

## What's Been Built

### Engine Startup (P0 — Fixed 2026-03-06)
- [x] Engine started via `/bin/bash` subprocess with absolute node path discovery
- [x] Wrapper script `/app/scripts/start_engine.sh` handles stdin + finds node binary
- [x] Backend stages `genesis-prompt.md` + `auto-config.json` + custom skills, then starts engine
- [x] Engine handles everything: wallet, API key provisioning, identity, constitution, SOUL, heartbeat, skills
- [x] **CRITICAL FIX**: automaton/node_modules was excluded from git (18,000+ files). Now tracked.
- [x] Removed automaton's nested .git so parent repo tracks all files
- [x] Fixed .gitignore — only frontend/node_modules excluded, .env files committed

### Dashboard (Read-Only Viewer)
- [x] 9 pages: Agent Mind, Fund HQ, Agents, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration
- [x] Live Engine Bridge reading all state from engine's SQLite state.db
- [x] 30+ API endpoints for full visibility
- [x] No demo/mock/fake data — real engine state or "waiting" when not started

## Key Files
- `/app/backend/server.py` — Main API (create, status, live data endpoints)
- `/app/backend/engine_bridge.py` — SQLite bridge to engine state
- `/app/scripts/start_engine.sh` — Engine launcher (finds node, pipes stdin)
- `/app/automaton/dist/index.js` — Built engine entry point
- `/app/automaton/node_modules/` — Runtime dependencies (MUST be in git)
- `/app/.gitignore` — Only excludes frontend/node_modules

## Deployment Checklist
- [x] .gitignore fixed (automaton node_modules included)
- [x] .env files tracked by git
- [x] No sudo/supervisorctl dependencies
- [x] Absolute paths for /bin/bash
- [x] start_engine.sh finds node at /usr/bin/node, /usr/local/bin/node, etc.

## Pending / Future
- Agent needs USDC funding to become fully operational (sleeps at $0 credits)
- Self-hosted infrastructure (move off Conway Cloud)
- AI agent creates its own smart contracts autonomously
