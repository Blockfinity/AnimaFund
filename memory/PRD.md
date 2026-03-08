# Anima Fund — Product Requirements Document

## Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform named "Anima Fund". Deploy and monitor multiple AI agents from a single dashboard, each with their own wallet, Telegram bot, goals, and revenue share to creator.

## Architecture
- **Frontend**: React (CRA) at port 3000
- **Backend**: FastAPI at port 8001 (modular router architecture)
- **Database**: MongoDB (agents collection, genesis state), SQLite (state.db per agent)
- **Agent Engine**: Conway Research Automaton (Node.js), bundled via esbuild
- **Multi-Agent**: Each agent gets isolated HOME dir at `~/agents/{id}/` with `$HOME/.automaton/` containing state.db, wallet, skills, config

## Backend Architecture (Refactored)
```
backend/
├── server.py              # Slim main: lifespan, CORS, health, router includes
├── database.py            # Shared MongoDB init/close/get_db
├── config.py              # Shared constants (AUTOMATON_DIR, ANIMA_DIR, etc.)
├── engine_bridge.py       # Live engine data bridge (reads state.db)
├── payment_tracker.py     # Financial enforcement
├── telegram_notify.py     # Telegram notification helper
└── routers/
    ├── agents.py          # Agent CRUD, skills listing
    ├── genesis.py         # Genesis creation, reset, wallet, engine management
    ├── live.py            # All /api/live/* endpoints (25+ endpoints)
    └── telegram.py        # Telegram send/status
```

## Multi-Agent Architecture
- Each agent: own HOME dir, own `.automaton/`, own wallet, own Telegram bot, own state.db
- Create from frontend: name, welcome message, genesis prompt, goals, SOL wallet, ETH wallet, revenue share %, TG bot token, TG chat ID
- Agent selector dropdown in dashboard header to switch between agents
- All dashboard pages automatically show data for selected agent
- Default "Anima Fund" agent at `~/.anima` is protected from deletion
- Engine starts with `HOME=/root/agents/{id}/` for full process isolation

## Financial Model
- 50% of all profit (after sustainability) to creator — configurable per agent
- Creator wallets: SOL + ETH (configurable per agent)
- $10K minimum to launch VC fund
- 3% mgmt fee, 20% carry when fund is active

## What's Been Implemented
- [x] Full 10-page dashboard (Agent Mind, Fund HQ, Agents, Skills, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration, Wallet & Logs)
- [x] Real-time engine bridge from state.db
- [x] Telegram integration — per-agent bots supported
- [x] 96 real skills (including gambling-mastery, rainbet-betting-mastery, negotiation-mastery)
- [x] 6 AI models
- [x] Payment compliance tracker
- [x] Security: secrets in .env, {{placeholders}} in prompts
- [x] Multi-Agent Dashboard with agent selector, full create modal with skill selector
- [x] Genesis Prompt v3: aggressive money-making, parallel execution
- [x] Backend refactored into modular FastAPI routers (from 1032-line monolith)
- [x] OPSEC hardening: genesis prompt + constitution forbid agents from revealing framework, codebase, keys, or secrets
- [x] Constitution Article XIII (Information Security & Open Collaboration) — protects secrets while enabling agent-to-agent collaboration
- [x] Push-constitution endpoint to update live agents without reset
- [x] Wallet mismatch detection: detects when engine wallet differs from config wallet, shows warning in UI
- [x] Wallet preservation: genesis/create backs up and restores wallet.json + anima.json to prevent new wallet generation
- [x] Adaptive polling: Dashboard polls 10s during sleep/critical, 3s when active (prevents UI thrashing)
- [x] CRITICAL: Full agent isolation — all endpoints read from active agent's data dir (state.db, SOUL.md, wallet, logs)
- [x] Agent selection persists across server restarts (file-based persistence)
- [x] Auto-select new agents after creation, frontend resets all state on switch
- [x] Full E2E tested: iterations 19-24 all 100% pass, deployment-ready

## API Endpoints
- `GET /api/health` — Health check
- `GET /api/agents` — List all agents
- `POST /api/agents/create` — Create with full config
- `POST /api/agents/{id}/select` — Switch dashboard data source
- `POST /api/agents/{id}/start` — Start agent engine (isolated HOME)
- `DELETE /api/agents/{id}` — Remove non-default agent
- `GET /api/skills/available` — List all 95 skills for creation modal
- `GET /api/payments/status` — Payment compliance
- `GET /api/genesis/status` — Genesis agent status
- `POST /api/genesis/create` — Create genesis agent
- `POST /api/genesis/reset` — Reset agent (preserves wallet)
- `GET /api/wallet/balance` — Real-time on-chain balance
- `GET /api/engine/live` — Engine live check
- `GET /api/engine/status` — Engine repo info
- `GET /api/engine/logs` — Engine stdout/stderr logs
- `GET /api/live/*` — 25+ live data endpoints (from selected agent's state.db)
- `POST /api/telegram/send` — Bot send
- `GET /api/telegram/status` — Telegram config check
- `GET /api/constitution` — Read constitution

## Upcoming Tasks
- Fund agents with Conway credits
- On production: Reset VC agent with new aggressive prompt
- Verify parallel execution in live agent logs
- Verify Telegram reporting from agents

## Future Tasks
- P2: Real smart contracts for trustless fee/revenue splits
- P2: Android Device Control
- P2: Self-hosted infrastructure migration
