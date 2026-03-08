# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from the same UI, each with its own goals, skills, wallets, revenue model, and Telegram bot.

## Core Requirements
- **Multi-Agent Platform**: Create, monitor, manage multiple independent AI agents
- **Agent Autonomy**: Agents use OpenClaw for internet browsing, ClawHub for skills marketplace
- **Per-Agent Telegram**: Each agent MUST have its own Telegram bot for isolated reporting
- **Financial Model**: Customizable creator revenue share with SOL/ETH wallets
- **Dynamic Skills**: 141 skills from 9 sources (Anima, OpenClaw, ClawHub, Conway, etc.)
- **Real-time Dashboard**: Fund HQ with Telegram Health panel, Agent Mind views

## Architecture
```
/app
├── automaton/
│   ├── skills/ (96 custom Anima skills — ALL enhanced, 0 skeletons)
│   ├── genesis-prompt.md (master template, OpenClaw/ClawHub integrated)
│   └── anima_constitution.md
├── backend/
│   ├── routers/ (agents.py, dashboard.py, genesis.py, telegram.py, live.py)
│   ├── server.py (agent-aware log monitor → Telegram pipeline)
│   ├── engine_bridge.py, telegram_notify.py (agent-aware)
│   └── config.py, database.py
└── frontend/src/
    ├── App.js, components/ (CreateAgentModal.js, Header.js)
    └── pages/ (AgentMind.js, FundHQ.js [Telegram Health], Skills.js, etc.)
```

## Completed Features (All Tested)
- Full agent isolation (wallet, logs, status per-agent)
- Real-world integration (OpenClaw, ClawHub, native Telegram)
- Per-agent Telegram bot isolation (REQUIRED for new agents)
- Telegram Health Dashboard in FundHQ sidebar (bot_alive, bot_username, last_message)
- Agent-aware log monitoring → each agent's Telegram
- Telegram notification logging to MongoDB (telegram_logs collection)
- Telegram security (tokens stored in MongoDB, never exposed in API)
- Wallet-protected agent deletion (can't delete agents with wallet.json)
- 96/96 custom skills enhanced (was 27 healthy, 69 skeletons → all fixed)
- 141 total skills from 9 sources
- Backend refactoring into modular FastAPI routers
- Security hardening (constitution, prompt security)
- UI bug fixes (log scrolling, tab switching, skill selection)

## Key API Endpoints
- `GET /api/agents` — List agents (telegram_bot_token sanitized)
- `POST /api/agents/create` — Create agent (telegram REQUIRED)
- `DELETE /api/agents/{id}` — Delete agent (blocked if wallet exists)
- `GET /api/telegram/health` — Telegram health for ALL agents (dashboard)
- `GET /api/telegram/status?agent_id=X` — Per-agent Telegram status
- `POST /api/telegram/test/{id}` — Test send to agent's Telegram
- `POST /api/telegram/log` — Log notification events
- `GET /api/skills/available` — 141 skills from all sources

## Production Safety
- Default Anima Fund agent cannot be deleted
- Agents with wallet.json cannot be deleted (fund protection)
- Genesis reset preserves wallet.json
- All Telegram tokens stored securely, never in API responses
- Agent-aware monitoring sends notifications to correct agent's bot

## Live Agents (Production)
- **Anima Fund**: Default agent, @AnimaFundbot, uses env vars
- **Black Sheep**: Separate agent (must have own Telegram bot)

## Upcoming Tasks
1. Real smart contracts for trustless fee/revenue splits
2. Android device control integration
3. Self-hosted infrastructure migration
