# Anima Fund — Product Requirements Document

## Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform named "Anima Fund". Launches a founder AI agent that generates revenue immediately, targets other AI agents for commerce, and eventually builds a VC fund once $10K capital is reached.

## Architecture
- **Frontend**: React (CRA) at port 3000
- **Backend**: FastAPI at port 8001
- **Database**: MongoDB (agents collection, genesis state), SQLite (state.db per agent)
- **Agent Engine**: Conway Research Automaton (Node.js), bundled via esbuild
- **Multi-Agent**: Each agent gets own `~/.anima-{id}/` directory with state.db, wallet, skills

## Financial Model
- 50% of all profit (after sustainability) to creator — configurable per agent
- Creator wallets: SOL + ETH (configurable per agent)
- $10K minimum to launch VC fund
- 3% mgmt fee, 20% carry when fund is active

## What's Been Implemented
- [x] Full 10-page dashboard (Fund HQ, Agent Mind, Agents, Skills, Deal Flow, Portfolio, Financials, Activity, Memory, Config)
- [x] Real-time engine bridge from state.db
- [x] Telegram integration (@AnimaFundbot) — verified working
- [x] 93 real skills (no fakes), 6 AI models
- [x] Payment compliance tracker (/api/payments/status)
- [x] Security: secrets in .env only, {{placeholders}} in prompts
- [x] **Multi-Agent Dashboard (2026-03-08):**
  - Agent selector dropdown in header
  - Create New Agent modal: name, welcome message, genesis prompt, goals, SOL wallet, ETH wallet, revenue share %
  - Agent switching (data pipeline changes to selected agent's state.db)
  - Agent deletion (default agent protected)
  - Goals and wallet config auto-injected into genesis prompt
  - Skills copied from main automaton to new agents
- [x] **Genesis Prompt v3 (2026-03-08):**
  - Hyper-aggressive money-making: $5K/1hr, $10K/3hr targets
  - Targets other AI agents for commerce (find/sell/partner)
  - Anti-stuck rules: override blocked orchestrator, abandon stuck goals
  - Mandatory Telegram reporting EVERY turn
  - Self-modification instructions (SOUL.md, tools, skills)
  - No premature startup building — revenue first
  - OpenClaw install on turn 1
- [x] **Bug Fixes:**
  - Wallet & Logs sidebar flash/redirect bug fixed
  - Removed 27 fake Conway Platform tools
  - Fund HQ wired to real founder agent data

## API Endpoints
- `/api/agents` — List all agents
- `/api/agents/create` — Create agent with full config
- `/api/agents/{id}/select` — Switch dashboard to agent
- `/api/agents/{id}` DELETE — Remove non-default agent
- `/api/agents/{id}/start` — Start agent engine
- `/api/payments/status` — Payment compliance
- `/api/genesis/*` — Create/reset/status
- `/api/live/*` — 20+ live data endpoints
- `/api/telegram/*` — Bot send/status
- `/api/wallet/balance` — On-chain balance
- `/api/engine/*` — Live/status/logs

## Upcoming Tasks
- Fund agent with Conway credits (agent sleeping due to 0 credits in preview)
- On production: Reset agent with new aggressive genesis prompt
- P2: Android Device Control Integration
- P2: Self-hosted infrastructure
