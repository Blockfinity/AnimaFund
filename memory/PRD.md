# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via the Conway Cloud platform.

## Architecture
- **Frontend**: React (CRA) + Shadcn/UI + Tailwind
- **Backend**: FastAPI + MongoDB (motor)
- **Agent Engine**: Conway Automaton (runs remotely on Conway Cloud)
- **Data Pipeline**: Telegram Bot API → MongoDB → Dashboard
- **Balance**: Conway API (api.conway.tech) + Base chain RPC (on-chain USDC/ETH)

## Core Requirements
1. Multi-agent dashboard to create, monitor, and manage independent AI agents
2. Real-time production logs from Telegram bot messages
3. Conway API integration for live credits/balance
4. Genesis prompt that properly bootstraps OpenClaw, Conway Terminal, MCP tools
5. Anti-loop/anti-stuck safeguards in agent behavior
6. Revenue tracking and financial monitoring
7. Infrastructure view (sandboxes, domains, tools)

## Key Files
- `/app/backend/routers/telegram_logs.py` — Telegram log ingestion pipeline
- `/app/backend/routers/genesis.py` — Agent creation, wallet, balance (includes Conway API)
- `/app/backend/routers/agents.py` — Agent CRUD, bootstrap, start
- `/app/backend/routers/live.py` — Live engine log streaming
- `/app/backend/routers/infrastructure.py` — Sandbox/domain/tool monitoring
- `/app/backend/engine_bridge.py` — Reads local state.db
- `/app/automaton/genesis-prompt.md` — Agent bootstrap prompt template
- `/app/scripts/bootstrap_agent.sh` — Pre-installs Conway Terminal, OpenClaw
- `/app/frontend/src/pages/AgentMind.js` — Main monitoring dashboard
- `/app/frontend/src/components/CreateAgentModal.js` — Agent creation form

## What's Been Implemented
- [2026-03-08] Initial platform build: React dashboard, FastAPI backend, MongoDB
- [2026-03-08] Agent creation flow with Telegram verification
- [2026-03-08] AgentMind monitoring dashboard with LIVE FEED, LOGS, TURNS tabs
- [2026-03-08] Infrastructure page for sandbox/domain/tool monitoring
- [2026-03-08] Bootstrap script for pre-installing Conway Terminal + OpenClaw
- [2026-03-08] UI flashing bug fix, deployment audit
- [2026-03-09] **Telegram Log Ingestion System** — Fetches production bot messages → MongoDB → Dashboard PRODUCTION tab
- [2026-03-09] **Conway API Balance Integration** — Real-time credits from api.conway.tech
- [2026-03-09] **Genesis Prompt Complete Rewrite** — Includes system tools install, Conway Terminal, OpenClaw, MCP config, anti-loop rules, revenue strategies
- [2026-03-09] **Dashboard PRODUCTION Tab** — Shows production Telegram logs with stats banner (messages, turns, errors, cost, Conway credits)
- [2026-03-09] **Balance Fix** — Wallet balance now queries Conway API instead of relying on stale local cache

## Current Production Agent Status
- Agent: "Anima Fund" — Running on Conway Cloud
- Wallet: 0x28a6B4047bB2275E7E1cf5c7aD427274E1C2Ff61
- Status: CRITICAL (0 credits, stuck in behavioral loop)
- ~11,000+ Telegram messages, ~10,000 turns
- Stuck in infinite ls -la / read_file loop (wasting 2-4c per turn)
- OpenClaw was NEVER installed, Conway Terminal never set up as MCP
- Root cause: Agent environment missing curl/git, orchestrator deadlock, no sandbox deployment

## Prioritized Backlog

### P0 — Critical
- [ ] Agent is stuck in behavioral loop — needs new agent creation with fixed genesis prompt
- [ ] Credits depleted ($0.00) — needs funding before new agent can be effective

### P1 — Important
- [ ] Test new genesis prompt with a freshly created agent
- [ ] Verify OpenClaw + Conway Terminal install works on Conway sandbox
- [ ] Add dashboard log search/filter capabilities
- [ ] Implement log retention policy (keep all, but optimize display)

### P2 — Enhancement
- [ ] Real smart contracts integration
- [ ] Android device control integration
- [ ] Self-hosted agent engine migration
- [ ] Advanced agent reasoning improvements
- [ ] Multi-agent communication dashboard
- [ ] Revenue/income tracking charts

## Test Reports
- /app/test_reports/iteration_4.json — 52/52 passed (previous build)
- /app/test_reports/iteration_40.json — 21/21 passed (Telegram logs + Conway balance)

## 3rd Party Integrations
- Conway Research Ecosystem (web4.ai / api.conway.tech)
- Conway Automaton Engine
- OpenClaw
- ClawHub
- Telegram Bot API
- Base Chain RPC (USDC/ETH balance)
