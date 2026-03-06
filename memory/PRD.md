# Anima Fund — Product Requirements Document

## Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform named "Anima Fund". The platform launches a "founder AI" agent that becomes self-sustaining through revenue-generating tasks, then builds a full VC firm by replicating itself and hiring other AI agents. The fund invests in AI startups with a 99% rejection rate, focusing on high-return opportunities.

## Architecture
- **Frontend**: React (CRA) at port 3000
- **Backend**: FastAPI at port 8001
- **Database**: MongoDB (for genesis state), SQLite (state.db managed by automaton engine)
- **Agent Engine**: Conway Research Automaton (Node.js), bundled into single file via esbuild
- **Native Addon**: better-sqlite3 .node file, loaded from /app/automaton/native/

## Core Components
1. **Automaton Engine** (`/app/automaton/`): The Node.js AI agent that handles wallet generation, API provisioning, heartbeat, and all autonomous operations
2. **Engine Bridge** (`/app/backend/engine_bridge.py`): Reads from the engine's state.db to supply live data to dashboard APIs
3. **Dashboard Frontend**: 9-page React app for monitoring agent operations

## Key Technical Decisions
- **esbuild Bundling**: All JS dependencies bundled into single `dist/bundle.mjs` (110K lines) via custom build script with bindings plugin
- **Native Addon Loading**: Custom esbuild plugin replaces `bindings` npm package with `process.dlopen()` from known `/app/automaton/native/` path
- **Cross-Architecture**: Separate native addons for x64 (production) and arm64 (preview), selected at runtime by `start_engine.sh`

## What's Been Implemented
- [x] Agent creation flow (non-interactive via auto-config.json)
- [x] Wallet generation and API key provisioning
- [x] Real-time Engine Console with live logs
- [x] Dashboard with 9 pages (Fund HQ, Agent Mind, etc.)
- [x] Engine bridge reading from state.db
- [x] **P0 FIX**: better-sqlite3 native addon loading without node_modules (2026-03-06)
- [x] UI fixes: button disable during creation, flicker prevention, accurate status display

## Pending / Backlog
### P1
- Implement real smart contracts (Solidity) for fees, carry, LP vehicle

### P2 / Future
- Self-hosted infrastructure (migrate from Conway public infra)
- Fund the agent with Conway credits for full autonomous operation

## API Endpoints
All prefixed with `/api`:
- `POST /api/genesis/create` — Start the engine
- `GET /api/genesis/status` — Agent status, wallet, stage
- `GET /api/health` — Health check
- `GET /api/engine/live` — Engine liveness
- `GET /api/engine/logs` — Engine stdout/stderr
- `GET /api/live/*` — Live data from state.db (identity, agents, turns, soul, etc.)
