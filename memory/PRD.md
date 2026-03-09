# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via the Conway Cloud platform.

## Architecture
- **Frontend**: React (CRA) + Shadcn/UI + Tailwind
- **Backend**: FastAPI + MongoDB (motor)
- **Agent Engine**: Conway Automaton (runs remotely on Conway Cloud)
- **Data Pipeline**: Agent → Dashboard Webhook API → MongoDB → Dashboard UI
- **Secondary Pipeline**: Agent → Telegram Bot (for mobile monitoring)
- **Balance**: Conway API (api.conway.tech) + Base chain RPC (on-chain USDC/ETH)

## Data Flow
```
Agent (on Conway Cloud)
  ├── POST /api/agent-logs/webhook  →  MongoDB agent_logs  →  Dashboard PRODUCTION tab
  └── Telegram sendMessage          →  Mobile monitoring (secondary)
Conway API (api.conway.tech)        →  /api/conway/balance  →  Dashboard balance display
Base Chain RPC                      →  /api/wallet/balance   →  Dashboard balance display
```

## Core Requirements
1. Multi-agent dashboard to create, monitor, and manage independent AI agents
2. Direct webhook pipeline: agent sends logs to dashboard API on every turn
3. Conway API integration for live credits/balance
4. Genesis prompt that properly bootstraps OpenClaw, Conway Terminal, MCP tools
5. Anti-loop/anti-stuck safeguards in agent behavior
6. Revenue tracking and financial monitoring
7. Infrastructure view (sandboxes, domains, tools)
8. Logs are NEVER deleted — all data persisted permanently

## Key Files
- `/app/backend/routers/agent_logs.py` — Webhook endpoint for direct agent log ingestion
- `/app/backend/routers/telegram_logs.py` — Legacy Telegram log access (kept for reference)
- `/app/backend/routers/genesis.py` — Agent creation, wallet, balance (includes Conway API)
- `/app/backend/routers/agents.py` — Agent CRUD, bootstrap, start
- `/app/backend/routers/live.py` — Live engine log streaming
- `/app/backend/routers/infrastructure.py` — Sandbox/domain/tool monitoring
- `/app/backend/engine_bridge.py` — Reads local state.db
- `/app/automaton/genesis-prompt.md` — Agent bootstrap prompt template
- `/app/scripts/bootstrap_agent.sh` — Pre-installs Conway Terminal, OpenClaw
- `/app/frontend/src/pages/AgentMind.js` — Main monitoring dashboard with PRODUCTION tab
- `/app/frontend/src/components/CreateAgentModal.js` — Agent creation form

## What's Been Implemented
- [2026-03-08] Initial platform build: React dashboard, FastAPI backend, MongoDB
- [2026-03-08] Agent creation flow with Telegram verification
- [2026-03-08] AgentMind monitoring dashboard with LIVE FEED, LOGS, TURNS tabs
- [2026-03-08] Infrastructure page for sandbox/domain/tool monitoring
- [2026-03-08] Bootstrap script for pre-installing Conway Terminal + OpenClaw
- [2026-03-08] UI flashing bug fix, deployment audit
- [2026-03-09] **Agent Webhook Log System** — Agent sends logs directly to `/api/agent-logs/webhook` → MongoDB → Dashboard PRODUCTION tab
- [2026-03-09] **Conway API Balance Integration** — Real-time credits from api.conway.tech
- [2026-03-09] **Genesis Prompt Complete Rewrite** — Includes:
  - System tools install (curl, git, wget)
  - Conway Terminal installation
  - OpenClaw + MCP configuration
  - Dashboard webhook reporting (every turn)
  - Telegram reporting (every 5 turns, secondary)
  - Anti-loop rules (never write same file twice, never repeat ls/find)
  - Revenue-first strategy with sandbox deployment
- [2026-03-09] **Dashboard PRODUCTION Tab** — Shows webhook-received logs with stats
- [2026-03-09] **Balance Fix** — Wallet balance queries Conway API instead of stale local cache

## Current Production Agent Status
- Agent: "Anima Fund" — Running on Conway Cloud
- Status: CRITICAL (0 credits, stuck in behavioral loop of ls -la / read_file)
- OpenClaw was NEVER installed, Conway Terminal never set up as MCP
- Root cause: Agent environment missing curl/git, orchestrator deadlock

## Prioritized Backlog

### P0 — Critical
- [ ] Create NEW agent with fixed genesis prompt (current agent is unrecoverable)
- [ ] Fund new agent with Conway credits before launch
- [ ] Verify agent sends logs to BOTH dashboard webhook AND Telegram

### P1 — Important
- [ ] Verify OpenClaw + Conway Terminal actually install on Conway sandbox
- [ ] Add dashboard log search/filter capabilities
- [ ] Test anti-loop rules in production

### P2 — Enhancement
- [ ] Real smart contracts integration
- [ ] Android device control integration
- [ ] Self-hosted agent engine migration
- [ ] Revenue/income tracking charts
- [ ] Multi-agent communication dashboard

## Test Reports
- /app/test_reports/iteration_4.json — 52/52 passed (previous build)
- /app/test_reports/iteration_40.json — 21/21 passed (Telegram logs + Conway balance)

## 3rd Party Integrations
- Conway Research Ecosystem (web4.ai / api.conway.tech)
- Conway Automaton Engine
- OpenClaw + ClawHub
- Telegram Bot API
- Base Chain RPC (USDC/ETH balance)
