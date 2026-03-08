# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI VC fund platform. Multi-agent platform where new AI agents can be created/managed from one UI, each with own goals, skills, wallets, revenue model, and Telegram bot.

## Architecture
```
/app
├── automaton/
│   ├── skills/ (96 custom — ALL enhanced)
│   ├── genesis-prompt.md (35 Conway tools, OpenClaw, ClawHub)
│   └── anima_constitution.md
├── backend/routers/ (agents, dashboard, genesis, telegram, live)
├── backend/ (server, engine_bridge, telegram_notify, config, database)
└── frontend/src/ (App, pages/AgentMind+FundHQ+Skills, components/CreateAgentModal)
```

## Completed Features
- **Agent Mind**: 3 tabs — LIVE FEED (default), LOGS, TURNS — with search/filter
- **Auto-scroll**: Ref-based, debounced (300ms), respects user scrolling
- **Per-agent Telegram isolation**: Required for new agents, verified via API
- **Conway toggle**: Checkbox in Create Agent to include/exclude 35 Conway tools
- **Telegram Health Dashboard**: FundHQ sidebar, shows bot alive/down/none per agent
- **Agent-aware monitoring**: Logs/state → each agent's Telegram
- **Wallet protection**: Can't delete agents with wallet.json
- **96/96 skills enhanced**, 141 total from 9 sources
- **35 Conway Terminal tools** documented (sandbox, PTY, domain, credits, x402, inference)
- **PUT endpoint**: Update existing agents' Telegram config
- **Security**: No localhost, no exposed secrets, tokens never in API responses

## Key API Endpoints
- POST /api/agents/create (telegram required, include_conway toggle)
- PUT /api/agents/{id}/telegram (update existing agent's bot)
- GET /api/telegram/health (dashboard)
- GET /api/skills/available (141 skills)

## Upcoming Tasks
1. Real smart contracts for trustless fee/revenue splits
2. Android device control integration
3. Self-hosted infrastructure migration
