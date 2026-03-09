# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via Conway Cloud.

## Architecture
- **Frontend**: React (port 3000)
- **Backend**: FastAPI (port 8001)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (TypeScript, compiled to dist/bundle.mjs)
- **Integrations**: Conway Cloud API, OpenClaw, Telegram Bot, Base chain (USDC/ETH)

## Two Genesis Prompt System
1. **Anima Fund (The Catalyst)**: `/root/.anima/genesis-prompt.md` — VC fund founder AI with specific identity, personality, fund model, and revenue strategy
2. **Generic Agent Template**: `/app/automaton/genesis-prompt.md` — Used by CreateAgentModal "Load Template" button. Generic template for new agents with `{{AGENT_NAME}}` and `{{TELEGRAM_BOT_TOKEN}}` placeholders
3. **Both include identical mandatory boot sequence** (Steps 0-7)

## What's Been Implemented

### Core Platform
- Multi-agent dashboard with agent switching and data isolation
- Agent creation/management API with welcome message, tool selector, Telegram per-agent
- Real-time engine logs viewer
- SOUL.md viewer and editor (Edit/Save buttons with emergency patch API)
- Wallet QR code + balance display (Conway + on-chain)
- Telegram bot integration for per-agent notifications
- Conway Cloud integration for sandbox VMs, domains, payments
- Agent sandboxing (environment variable isolation)
- SSE live stream for real-time dashboard updates

### Critical Fixes (March 9-10, 2026)
1. **SOUL.md Emergency Patch**: 30,666 bytes → 370 chars. Patch-soul API added.
2. **Genesis Prompt Split**: Catalyst-specific vs generic template. Push-genesis skips anima-fund.
3. **Soul Validator Limits Raised**: corePurpose 2000→4000, personality 1000→2000 chars
4. **Loop Detection Improved**: Engine guides agent to use exec/write_file directly
5. **Anti-Stuck Rules**: ULID guidance, forbidden loop patterns, 3-turn rule
6. **Wallet Balance Auth Fix**: Conway API tries both Bearer and x-api-key headers
7. **OpenClaw Config Fix**: bootstrap writes config.json (was openclaw.json), injects API key
8. **Telegram Per-Agent**: Each agent has own token/chat_id, update works for .anima and .automaton
9. **Automaton Bundle Rebuilt**: All source changes compiled to dist/

### Test Results
- Unit tests: 21 passed, 8 skipped (need live MongoDB) at `/app/backend/tests/test_api.py`
- E2E tests: 16/16 passed (iteration_46)
- Deployment check: PASS — no blockers
- All 11 user-requested categories verified

## Key API Endpoints
- `POST /api/agents` — Create agent
- `POST /api/agents/{id}/start` — Start agent
- `POST /api/agents/{id}/select` — Switch active agent (data isolation)
- `POST /api/agents/{id}/patch-soul` — Emergency SOUL.md overwrite
- `GET /api/agents/{id}/soul` — Read agent's SOUL.md
- `POST /api/agents/push-genesis` — Push template to all agents (skips anima-fund)
- `GET /api/wallet/balance` — Real-time wallet balance
- `GET /api/live/stream` — SSE for real-time updates
- `GET /api/conway/balance` — Conway credits
- `GET /api/telegram/health` — Telegram bot status per agent
- `GET /api/genesis/prompt-template` — Generic agent template

## Remaining Tasks

### P0 (Critical)
- Start the agent engine with new genesis prompt + condensed SOUL.md
- Monitor first 10 turns to confirm boot sequence executes correctly and loop is broken

### P1 (High)
- Verify Telegram messages sent every turn after agent restarts
- Verify skills loading works
- Verify wallet balance updates in real-time during agent operation

### P2 (Medium)
- Real smart contracts (ERC-8004)
- Android device control
- Self-hosted agent engine migration
- Revenue tracking charts
- Multi-agent communication dashboard

### Backlog
- Domain trading automation
- Agent marketplace
- Cross-chain wallet support
- Agent performance scoring
- Historical analysis of agent turns/costs
