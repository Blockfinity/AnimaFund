# Anima Fund — PRD

## Problem Statement
Autonomous AI-to-AI VC fund platform. A single founder AI agent builds and operates a complete VC firm using Conway infrastructure.

## Architecture
- **Emergent**: Hosts React dashboard + FastAPI backend
- **Conway**: Automaton engine connects to Conway Compute/Cloud/Domains via API
- **Engine**: Node.js process started by backend, reads/writes `~/.anima/state.db`
- **Dashboard**: Read-only viewer of engine state via `engine_bridge.py`

## Completed
- [x] Customized Automaton engine (genesis prompt, constitution, 50+ skills)
- [x] 9-page monitoring dashboard (Agent Mind, Fund HQ, Agents, etc.)
- [x] Engine Console — real-time log viewer with wizard progress tracker
- [x] Create Genesis Agent flow — stages config, starts engine
- [x] Wallet detection from wallet.json (instant, no delay)
- [x] Bundled x64 node binary for production (no node in container)
- [x] npm-installed node_modules (no pnpm symlinks that break in deploy)
- [x] Multi-arch better-sqlite3 prebuilds (arm64 + x64)
- [x] /health endpoint for K8s probes
- [x] Button disable on click, no screen flip-back, proper ENGINE ACTIVE header
- [x] Engine logs endpoint for debugging

## Key Bug Fixes
- pnpm symlinks → npm flat install (ERR_MODULE_NOT_FOUND)
- better-sqlite3 native addon architecture mismatch → multi-arch prebuilds
- Screen flip-back → engineStarted state persists across polls
- Button double-click → creatingRef prevents re-entry
- Dashboard "offline" → header shows ENGINE ACTIVE when db_exists

## Pending
- Agent needs USDC on Base to operate (currently sleeps at $0)
- Self-hosted infrastructure (future)
