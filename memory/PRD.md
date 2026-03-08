# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from the same UI, each with its own goals, skills, wallets, revenue model, and Telegram bot.

## Core Requirements
- **Multi-Agent Platform**: Create, monitor, manage multiple independent AI agents
- **Agent Autonomy**: Agents use OpenClaw for internet browsing, ClawHub for skills marketplace
- **Per-Agent Telegram**: Each agent MUST have its own Telegram bot for isolated reporting
- **Financial Model**: Customizable creator revenue share with SOL/ETH wallets
- **Dynamic Skills**: 141 skills from 9 sources (Anima, OpenClaw, ClawHub, Conway, etc.)
- **Real-time Dashboard**: Fund HQ and Agent Mind views with agent selector

## Architecture
```
/app
├── automaton/
│   ├── skills/ (96 custom Anima skills — all enhanced, no skeletons)
│   ├── genesis-prompt.md (master template, OpenClaw/ClawHub integrated)
│   └── anima_constitution.md
├── backend/
│   ├── routers/ (agents.py, dashboard.py, genesis.py, telegram.py, live.py)
│   ├── server.py, engine_bridge.py, telegram_notify.py (agent-aware)
│   └── config.py, database.py
└── frontend/src/
    ├── App.js, components/ (CreateAgentModal.js, Header.js)
    └── pages/ (AgentMind.jsx, Skills.js, etc.)
```

## Completed Features
- Full agent isolation (wallet, logs, status per-agent)
- Real-world integration (OpenClaw, ClawHub, native Telegram)
- Per-agent Telegram bot isolation (REQUIRED for new agents)
- Telegram security (tokens stored in MongoDB, never exposed in API)
- 96/96 custom skills enhanced (was 27 healthy, 69 skeletons)
- 141 total skills from 9 sources
- Backend refactoring into modular FastAPI routers
- Security hardening (constitution, prompt security)
- UI bug fixes (log scrolling, tab switching, skill selection)

## Key API Endpoints
- `GET /api/agents` — List agents (telegram_bot_token sanitized)
- `POST /api/agents/create` — Create agent (telegram REQUIRED)
- `POST /api/agents/select/{id}` — Set active agent
- `GET /api/skills/available` — 141 skills from all sources
- `GET /api/telegram/status?agent_id=X` — Per-agent Telegram status
- `POST /api/telegram/test/{id}` — Test send to agent's Telegram

## Live Agents (Production)
- **Anima Fund**: Default agent, uses env vars for Telegram
- **Black Sheep**: Separate agent (must have own Telegram bot)

## Upcoming Tasks
1. Review live agents (Anima Fund, Black Sheep) — verify own Telegram bots in production
2. Verify agents performing outside sandbox in production
3. Real smart contracts for trustless fee/revenue splits
4. Android device control integration
5. Self-hosted infrastructure migration
