# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via Conway Cloud.

## Architecture
- **Frontend**: React (port 3000)
- **Backend**: FastAPI (port 8001)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (TypeScript, compiled to dist/bundle.mjs)
- **Integrations**: Conway Cloud API, OpenClaw, Telegram Bot, Base chain (USDC/ETH)

## What's Been Implemented

### Core Platform
- Multi-agent dashboard with agent switching
- Agent creation/management API
- Real-time engine logs viewer
- SOUL.md viewer and editor (with emergency patch API)
- Wallet QR code + balance display
- Telegram bot integration for notifications
- Conway Cloud integration for sandbox VMs, domains, payments
- Agent sandboxing (environment variable isolation)

### Critical Fixes (March 9, 2026)
1. **SOUL.md Emergency Patch**: Direct overwrite from 30,666 bytes to 726 chars, bypassing update_soul char limits
2. **Genesis Prompt Rewrite**: Removed "already available" assumption, added mandatory boot sequence, anti-stuck rules with ULID guidance, Telegram reporting every turn, skill loading steps
3. **Soul Validator Limits Raised**: corePurpose 2000→4000, personality 1000→2000 chars
4. **Loop Detection Improved**: Engine loop messages now guide agent to use exec/write_file/sandbox_create directly instead of looping on create_goal
5. **Wallet Balance Auth Fix**: Conway API now tries both Bearer and x-api-key headers
6. **OpenClaw Config Fix**: Bootstrap writes to config.json (was openclaw.json), injects Conway API key
7. **SSE Live Stream**: New /api/live/stream endpoint for real-time dashboard updates
8. **Frontend SOUL.md Editor**: Edit/Save buttons in Agent Mind dashboard for emergency soul patches
9. **Automaton Bundle Rebuilt**: All source changes compiled to dist/

## Key API Endpoints
- `POST /api/agents` — Create agent
- `POST /api/agents/{id}/start` — Start agent
- `POST /api/agents/{id}/patch-soul` — Emergency SOUL.md overwrite
- `GET /api/agents/{id}/soul` — Read agent's SOUL.md
- `GET /api/wallet/balance` — Real-time wallet balance (Conway + on-chain)
- `GET /api/live/stream` — SSE for real-time updates
- `GET /api/conway/balance` — Conway credits balance
- `GET /api/engine/live` — Engine status
- `GET /api/engine/logs` — Engine stdout/stderr logs

## Key Files
- `/app/automaton/genesis-prompt.md` — Genesis prompt template (rewritten)
- `/app/automaton/src/soul/validator.ts` — Soul validation limits
- `/app/automaton/src/agent/loop.ts` — Loop detection logic
- `/app/backend/routers/genesis.py` — Genesis, wallet, patch-soul APIs
- `/app/backend/routers/live.py` — Live data + SSE stream
- `/app/backend/engine_bridge.py` — State.db reader
- `/app/scripts/bootstrap_agent.sh` — Agent bootstrap script
- `/root/.anima/SOUL.md` — Live agent's soul (726 chars)
- `/root/.anima/genesis-prompt.md` — Staged genesis prompt for agent

## Remaining Tasks

### P0 (Critical)
- Start/restart the agent engine with the new genesis prompt and condensed SOUL.md, monitor first 10 turns to confirm loop is broken

### P1 (High)
- Verify Conway wallet balance accuracy after agent starts running
- Confirm Telegram messages are being sent every turn
- Verify skills are being loaded and used

### P2 (Medium)
- Implement real smart contracts (ERC-8004)
- Android device control integration
- Self-hosted agent engine migration
- Revenue tracking charts
- Multi-agent communication dashboard
- Historical analysis of agent turns/costs

### Backlog
- Domain trading automation
- Agent marketplace
- Cross-chain wallet support
- Agent performance scoring
