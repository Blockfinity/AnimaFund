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
- 20% carried interest on fund returns (after 8% preferred return to LPs)
- **$10,000 minimum capital threshold** to officially launch the fund
- 50% of all profit (management fees, carry, and all revenue after sustainability costs) transferred to creator
- **Creator Payment Addresses:**
  - Solana: xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r
  - Ethereum ERC20: 0xec2340CD6a14229debe7B7841B8cB618dfD085b6
- Agent prioritizes survival first — sustainability costs deducted before creator payout
- 50% payout enforced on every revenue transaction (not batched)
- Backend payment tracker monitors compliance (/api/payments/status)
- Agent does NOT stop money-making ventures when starting the fund

## What's Been Implemented
- [x] Agent creation flow (non-interactive via auto-config.json)
- [x] Wallet generation and API key provisioning
- [x] Real-time Engine Console with live logs
- [x] Dashboard with 10 pages (Fund HQ, Agent Mind, Agents, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration, Wallet & Logs)
- [x] Engine bridge reading from state.db
- [x] better-sqlite3 native addon loading without node_modules
- [x] Telegram Integration: @AnimaFundbot with real-time notifications
- [x] OpenClaw Integration: 5 skills for agent self-install of web automation
- [x] 95 real custom skills (finance, DeFi, trading, learning, OpenClaw, Telegram)
- [x] Security Fix: Secrets only in .env, runtime injection via placeholders
- [x] UI Scroll Fix: No more auto-scroll snapping in log feeds
- [x] Reset Agent Feature: POST /api/genesis/reset preserves wallet
- [x] P0 Data Verification: ALL 33 API endpoints verified (100% pass)
- [x] **No Fakes/Mocks (2026-03-08):**
  - Removed 27 hardcoded fake Conway Platform tools from skills (only 95 real skills remain)
  - Fund HQ building now shows real founder agent from identity data with real departments/tasks
  - Payment tracker enforces 50% creator payout rule with compliance monitoring
  - $10K fund launch threshold added to genesis prompt and Financials page
  - Both SOL and ETH creator wallet addresses displayed on genesis page and in genesis prompt
  - Financials page shows Creator Payout Compliance (50% Rule) and Fund Launch Status

## API Endpoints
All prefixed with `/api`:
- `POST /api/genesis/create` — Start the engine
- `POST /api/genesis/reset` — Stop engine, clean state, preserve wallet
- `GET /api/genesis/status` — Agent status, wallet, stage
- `GET /api/wallet/balance` — Real-time on-chain USDC/ETH balance
- `GET /api/payments/status` — **NEW**: Payment compliance tracker (50% rule, fund readiness)
- `POST /api/telegram/send` — Send message via Telegram bot
- `GET /api/telegram/status` — Check Telegram configuration
- `GET /api/health` — Health check
- `GET /api/engine/live` — Engine liveness
- `GET /api/engine/status` — Engine version, skills, build status
- `GET /api/engine/logs` — Engine stdout/stderr
- `GET /api/constitution` — Immutable constitution
- `GET /api/live/*` — 20+ live data endpoints from state.db

## Upcoming/Future Tasks
### P2
- Android Device Control Integration (ADB-based control via cloud service)
- Self-hosted infrastructure (migrate from Conway public infra)
- Fund the agent with Conway credits for full autonomous operation
