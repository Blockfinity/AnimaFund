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
- [x] Dashboard with 10 pages (Fund HQ, Agent Mind, Agents, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration, Wallet & Logs)
- [x] Engine bridge reading from state.db
- [x] **P0 FIX**: better-sqlite3 native addon loading without node_modules (2026-03-06)
- [x] UI fixes: button disable during creation, flicker prevention, accurate status display
- [x] **Deployment hardening**: Untracked node_modules, fixed dist/index.js references (2026-03-07)
- [x] **Agent Mind — Live Logs**: LOGS/TURNS tabs, color-coded real-time engine logs with tags (ERROR, CRITICAL, THINK, SLEEP, HEARTBEAT, STATE, LOOP) (2026-03-07)
- [x] **Wallet & Funding from Dashboard**: Wallet QR code, copyable address, funding instructions (Conway credits, USDC on Base, Conway Cloud link) in Agent Mind right panel (2026-03-07)
- [x] **Dashboard ↔ Wallet Navigation**: "Wallet & Logs" sidebar nav returns to genesis/wallet screen; "Open Dashboard" button returns to dashboard (2026-03-07)
- [x] **SQL Column Fix (P0)**: Fixed ALL SQL queries in engine_bridge.py from camelCase to snake_case column names. This was a systemic bug silently breaking every data endpoint (2026-03-07)
- [x] **Activity page**: Shows real heartbeat events (38+), 53 skills, with tabs for Heartbeat/Tool Calls/Messages/Skills (2026-03-07)
- [x] **Memory page**: Shows 16 KV store items, 8 wake events, with tabs for Runtime State/Wake Events/Semantic Memory (2026-03-07)
- [x] **Agents page**: Shows Founder Agent identity, 6 heartbeat schedule tasks with cron expressions, with tabs for Founder/Children/Discovered/Heartbeat Tasks (2026-03-07)
- [x] **Fund HQ**: Falls back to heartbeat events when no tool call activity (2026-03-07)
- [x] **New API endpoints**: /api/live/kv, /api/live/wake-events, /api/live/heartbeat-schedule, /api/live/skills-full (2026-03-07)
- [x] **Skills Page**: Dedicated page showing 80 skills (53 Anima Fund + 27 Conway Platform), 6 AI models. Filters: by source (Anima/Conway/MCP/OpenClaw), by agent, sort (A-Z/Most Used/Recently Acquired), search. Skills grouped by category. Model registry table. (2026-03-07)
- [x] **Real-Time On-Chain Balance**: `/api/wallet/balance` endpoint queries Base blockchain RPC directly for USDC/ETH balance, bypassing agent's 5-minute cycle. Integrated into Agent Mind dashboard with LIVE indicator. (2026-03-07)
- [x] **P0 Verification (2026-03-07)**: All P0 features verified — real-time balance display, all API endpoints, frontend navigation, genesis screen, dashboard pages. Testing: 96% backend (55/57 pass, 2 expected due to sleeping engine), 100% frontend.
- [x] **Deployment Hardening v2 (2026-03-07)**: Removed eth-account and all eth-* blockchain libraries (deployment blocker). Simplified wallet address fallback to read from wallet.json directly. Deleted dead frontend files (AgentNetwork.js, Overview.js). Deleted obsolete dist/better-sqlite3-shim.mjs. Deployment agent: ALL CHECKS PASS.
- [x] **Genesis Config Fix (2026-03-07)**: Fixed agent not receiving creatorMessage and proper genesisPrompt on first boot. Patched bundle.mjs to pass autoConfig.creatorMessage to createConfig(). Added ~/.automaton → ~/.anima symlink for path consistency. Added POST /api/genesis/reset endpoint. Testing: 96% backend, 100% frontend.
- [x] **Telegram Integration (2026-03-07)**: Real-time Telegram notifications via @AnimaFundbot. Backend monitor watches engine state.db and sends alerts for state changes, turns, balance updates, errors. Agent skill teaches it to send Telegram messages via exec+curl. Endpoints: GET /api/telegram/status, POST /api/telegram/send. Testing: 100% (15/15 backend, 100% frontend).

## Deployment Hardening (2026-03-07)
- [x] Untracked `automaton/node_modules/` from git (17K files removed, not needed at runtime)
- [x] Untracked 429 old TypeScript dist files (only `bundle.mjs` remains in dist/)
- [x] Tracked `frontend/yarn.lock` for consistent builds
- [x] Updated `.gitignore` to exclude automaton/node_modules/, old dist files
- [x] Fixed `dist/index.js` → `dist/bundle.mjs` references in server.py (creation check + status endpoint)
- [x] Fixed `pgrep` pattern to match `dist/bundle.mjs` instead of `dist/index.js`
- [x] Verified bundle works WITHOUT `node_modules/` present (production simulation)
- [x] Git repo reduced from 18,000+ tracked files to 318
- [x] Deployment agent: PASS — all checks green
- [x] E2E test passed: create → wallet → provisioning → running → live data
### P1
- Implement real smart contracts (Solidity) for fees, carry, LP vehicle

### P2 / Future
- Self-hosted infrastructure (migrate from Conway public infra)
- Fund the agent with Conway credits for full autonomous operation

## API Endpoints
All prefixed with `/api`:
- `POST /api/genesis/create` — Start the engine (stages genesisPrompt + creatorMessage in auto-config)
- `POST /api/genesis/reset` — Stop engine, clean state, preserve wallet
- `GET /api/genesis/status` — Agent status, wallet, stage
- `GET /api/wallet/balance` — Real-time on-chain USDC/ETH balance via Base RPC
- `POST /api/telegram/send` — Send custom message to creator's Telegram
- `GET /api/telegram/status` — Check Telegram configuration status
- `GET /api/health` — Health check
- `GET /api/engine/live` — Engine liveness
- `GET /api/engine/logs` — Engine stdout/stderr
- `GET /api/live/*` — Live data from state.db (identity, agents, turns, soul, etc.)
