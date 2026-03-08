# Anima Fund — Product Requirements Document

## Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform named "Anima Fund". The platform launches a "founder AI" agent that becomes self-sustaining through revenue-generating tasks, then builds a full VC firm by replicating itself and hiring other AI agents. The fund invests in AI startups with a 99% rejection rate, focusing on high-return opportunities.

## Architecture
- **Frontend**: React (CRA) at port 3000
- **Backend**: FastAPI at port 8001
- **Database**: MongoDB (for genesis state), SQLite (state.db managed by automaton engine)
- **Agent Engine**: Conway Research Automaton (Node.js), bundled into single file via esbuild
- **Native Addon**: better-sqlite3 .node file, loaded from /app/automaton/native/

## Financial Model
- 3% management fee on AUM (annual, calculated and collected monthly)
- 20% carried interest on fund returns
- 50% of all profit (management fees, carry, and all revenue after sustainability costs) transferred to creator's Solana wallet: xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r
- Agent prioritizes survival first — sustainability costs deducted before creator payout
- Financial model is enforced via genesis prompt instructions (not smart contracts)

## Core Components
1. **Automaton Engine** (`/app/automaton/`): The Node.js AI agent that handles wallet generation, API provisioning, heartbeat, and all autonomous operations
2. **Engine Bridge** (`/app/backend/engine_bridge.py`): Reads from the engine's state.db to supply live data to dashboard APIs
3. **Dashboard Frontend**: 10-page React app for monitoring agent operations

## What's Been Implemented
- [x] Agent creation flow (non-interactive via auto-config.json)
- [x] Wallet generation and API key provisioning
- [x] Real-time Engine Console with live logs
- [x] Dashboard with 10 pages (Fund HQ, Agent Mind, Agents, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration, Wallet & Logs)
- [x] Engine bridge reading from state.db
- [x] better-sqlite3 native addon loading without node_modules
- [x] UI fixes: button disable during creation, flicker prevention, accurate status display
- [x] Deployment hardening: Untracked node_modules, fixed dist/index.js references
- [x] Agent Mind — Live Logs: LOGS/TURNS tabs, color-coded real-time engine logs
- [x] Wallet & Funding from Dashboard: Wallet QR code, copyable address, funding instructions
- [x] Dashboard ↔ Wallet Navigation
- [x] SQL Column Fix: Fixed ALL SQL queries in engine_bridge.py
- [x] Activity page: Heartbeat/Tool Calls/Messages/Skills tabs
- [x] Memory page: Runtime State/Wake Events/Semantic Memory tabs
- [x] Agents page: Founder/Children/Discovered/Heartbeat Tasks tabs
- [x] Fund HQ: Building visualization with departments and agents
- [x] New API endpoints: /api/live/kv, /api/live/wake-events, /api/live/heartbeat-schedule, /api/live/skills-full
- [x] Skills Page: 122 skills (95 Anima + 27 Conway Platform), 6 AI models, filters, search, sort
- [x] Real-Time On-Chain Balance: USDC/ETH via Base blockchain RPC
- [x] Genesis Config Fix: auto-config.json with creatorMessage and genesisPrompt
- [x] Telegram Integration: @AnimaFundbot with real-time notifications
- [x] OpenClaw Integration: 5 skills for agent self-install of web automation
- [x] 87 custom skills (finance, DeFi, trading, learning, OpenClaw, Telegram)
- [x] Security Fix: Secrets only in .env, runtime injection via placeholders
- [x] UI Scroll Fix: No more auto-scroll snapping in log feeds
- [x] Reset Agent Feature: POST /api/genesis/reset preserves wallet
- [x] **P0 Verification Complete (2026-03-08)**: ALL 33 API endpoints verified (64/64 backend tests pass), all 10 frontend pages verified (100% pass). Full data connection audit complete.
- [x] Revenue text updated to reflect "50% of all profit after sustainability costs"

## API Endpoints
All prefixed with `/api`:
- `POST /api/genesis/create` — Start the engine
- `POST /api/genesis/reset` — Stop engine, clean state, preserve wallet
- `GET /api/genesis/status` — Agent status, wallet, stage
- `GET /api/wallet/balance` — Real-time on-chain USDC/ETH balance
- `POST /api/telegram/send` — Send message via Telegram bot
- `GET /api/telegram/status` — Check Telegram configuration
- `GET /api/health` — Health check
- `GET /api/engine/live` — Engine liveness
- `GET /api/engine/status` — Engine version, skills, build status
- `GET /api/engine/logs` — Engine stdout/stderr
- `GET /api/constitution` — Immutable constitution
- `GET /api/live/*` — 20+ live data endpoints from state.db

## P1 Assessment (Smart Contracts) — NOT NECESSARY
The genesis prompt already enforces the 50% revenue split. The Conway platform handles all financial operations internally. Smart contracts would add trustless on-chain enforcement but are not needed for the current operational model. Can be revisited when managing real LP capital at scale.

## Upcoming/Future Tasks
### P2
- Android Device Control Integration (ADB-based control via cloud service)
- Self-hosted infrastructure (migrate from Conway public infra)
- Fund the agent with Conway credits for full autonomous operation
