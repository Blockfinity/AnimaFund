# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI VC fund platform. Multi-agent platform where new AI agents can be created and managed from the same UI, each with its own goals, skills, wallets, revenue model, and Telegram bot.

## Architecture
```
/app
├── automaton/skills/ (96 custom skills — all enhanced)
├── backend/routers/ (agents.py, dashboard.py, genesis.py, telegram.py, live.py)
├── backend/ (server.py, engine_bridge.py, telegram_notify.py, config.py, database.py)
└── frontend/src/ (App.js, pages/, components/)
```

## Completed Features
- Full agent isolation (wallet, logs, status per-agent)
- Per-agent Telegram bot isolation (REQUIRED for new agents, verified via API)
- PUT endpoint to update existing agents' Telegram config (/api/agents/{id}/telegram)
- Telegram Health Dashboard in FundHQ sidebar
- Agent-aware log monitoring → each agent's Telegram
- Create Agent flow verifies Telegram connection (getMe + sendMessage) before saving
- Telegram tokens stored in MongoDB, never exposed in API responses
- Wallet-protected agent deletion (can't delete agents with wallet.json)
- Auto-scroll fix: ref-based, debounced (300ms), respects user reading (no snapping)
- Tab switching (LOGS/TURNS) without page snapping (removed activeTab from fetchData deps)
- 96/96 custom skills enhanced, 141 total from 9 sources
- Security audit: no localhost/sandbox/exposed secrets in production code
- All sidebar items restored including Wallet & Logs

## Key API Endpoints
- GET /api/agents — List (token sanitized)
- POST /api/agents/create — Create (telegram REQUIRED, verified)
- PUT /api/agents/{id}/telegram — Update existing agent's Telegram config
- DELETE /api/agents/{id} — Delete (blocked if wallet exists)
- GET /api/telegram/health — Telegram health dashboard
- POST /api/telegram/test/{id} — Test send
- GET /api/skills/available — 141 skills

## Production Safety
- Default agent cannot be deleted
- Agents with wallets cannot be deleted
- Genesis reset preserves wallet.json
- Telegram tokens never in API responses

## Upcoming Tasks
1. Real smart contracts for trustless fee/revenue splits
2. Android device control integration
3. Self-hosted infrastructure migration
