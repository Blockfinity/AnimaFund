# Anima Fund — Product Requirements Document

## Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform named "Anima Fund". Deploy and monitor multiple AI agents from a single dashboard, each with their own wallet, Telegram bot, goals, and revenue share to creator.

## Architecture
- **Frontend**: React (CRA) at port 3000
- **Backend**: FastAPI at port 8001
- **Database**: MongoDB (agents collection, genesis state), SQLite (state.db per agent)
- **Agent Engine**: Conway Research Automaton (Node.js), bundled via esbuild
- **Multi-Agent**: Each agent gets isolated HOME dir at `~/agents/{id}/` with `$HOME/.automaton/` containing state.db, wallet, skills, config

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
- [x] Full 10-page dashboard
- [x] Real-time engine bridge from state.db
- [x] Telegram integration — per-agent bots supported
- [x] 93 real skills (no fakes), 6 AI models
- [x] Payment compliance tracker
- [x] Security: secrets in .env, {{placeholders}} in prompts
- [x] Multi-Agent Dashboard with agent selector, full create modal
- [x] Genesis Prompt v3: aggressive money-making, targets AI agents
- [x] Weather trading bot skill (Polymarket + Simmer SDK)
- [x] Wallet & Logs flash bug fixed
- [x] Full E2E tested: iterations 14-18 all 100% pass

## API Endpoints
- `GET /api/agents` — List all agents
- `POST /api/agents/create` — Create with full config (name, prompt, goals, wallets, revenue%, telegram)
- `POST /api/agents/{id}/select` — Switch dashboard data source
- `POST /api/agents/{id}/start` — Start agent engine (isolated HOME)
- `DELETE /api/agents/{id}` — Remove non-default agent
- `GET /api/payments/status` — Payment compliance
- `GET /api/live/*` — 20+ live data endpoints (from selected agent's state.db)
- `POST /api/telegram/send` — Bot send
- All genesis/engine/wallet endpoints

## Upcoming Tasks
- Fund agents with Conway credits
- On production: Reset VC agent with new aggressive prompt
- P2: Android Device Control, Self-hosted infra
