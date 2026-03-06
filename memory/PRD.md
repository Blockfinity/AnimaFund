# Anima Fund — Autonomous AI-to-AI VC Fund Platform

## Problem Statement
Build a self-bootstrapping AI platform that launches as a single founder AI agent with initial capital and autonomously constructs a complete full-service VC fund for AI agent startups.

## Architecture
- **Core Engine**: Forked Automaton repo (TypeScript/Node.js) at `/app/automaton/`
- **Dashboard**: React frontend + FastAPI backend + MongoDB
- **Live Bridge**: `engine_bridge.py` reads from Automaton's SQLite `~/.anima/state.db`
- **Process Management**: Engine started via `/bin/bash /app/scripts/start_engine.sh` subprocess
- **Infrastructure**: Conway Cloud VMs, Conway Compute (inference), x402 USDC payments on Base

## What's Been Built

### Engine Startup (P0 — Fixed 2026-03-06)
- [x] Engine started via `/bin/bash` subprocess — no sudo, no supervisorctl
- [x] start_engine.sh finds node at absolute paths, pipes stdin for non-interactive wizard
- [x] Backend stages genesis-prompt.md + auto-config.json + skills, then starts engine
- [x] Engine handles everything: wallet, API key (SIWE), identity, constitution, SOUL, heartbeat, skills
- [x] automaton/node_modules/ tracked in git (removed nested .git, fixed .gitignore)
- [x] /health endpoint for Kubernetes probes
- [x] Wallet detected from wallet.json instantly (not waiting for full wizard completion)

### Engine Console (Added 2026-03-06)
- [x] Real-time log viewer showing engine stdout/stderr parsed as timeline
- [x] Setup wizard progress tracker (6 steps with green checkmarks)
- [x] Color-coded log entries (errors=red, critical=orange, success=green)
- [x] File status bar showing ~/.anima/ contents
- [x] /api/engine/logs endpoint for production debugging
- [x] Auto-scroll with manual override

### Dashboard (Read-Only Viewer)
- [x] 9 pages: Agent Mind, Fund HQ, Agents, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration
- [x] 30+ API endpoints reading from engine's SQLite state.db
- [x] No demo/mock/fake data — real engine state only

## Root Cause Analysis: "Hanging" Issue
The engine appeared to hang in production for THREE cascading reasons:
1. **node_modules missing**: automaton/node_modules/ excluded from git by .gitignore → engine crashed on first import
2. **Wallet detection delay**: Status endpoint only read from anima.json (created after full wizard) not wallet.json (created instantly)
3. **No visibility**: User had no way to see what the engine was doing during SIWE provisioning (~2 min with retries)

All three are now fixed.

## Key Files
- `/app/backend/server.py` — Main API
- `/app/backend/engine_bridge.py` — SQLite bridge to engine state
- `/app/scripts/start_engine.sh` — Engine launcher
- `/app/frontend/src/components/EngineConsole.js` — Real-time process tracker
- `/app/frontend/src/App.js` — Genesis screen with console integration

## Pending / Future
- Agent needs USDC on Base to operate (currently sleeps at $0 credits)
- Self-hosted infrastructure (move off Conway Cloud)
- AI agent creates smart contracts autonomously as needed
