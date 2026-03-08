# Anima Fund - PRD

## Problem Statement
Fully autonomous AI-to-AI VC fund platform built on Conway Automaton + OpenClaw + ClawHub. Multi-agent system where each agent is permissionless — installs its own tools, discovers skills, operates without user intervention.

## Architecture
- **Frontend**: React (port 3000) — viewer/dashboard for agent data
- **Backend**: FastAPI (port 8001) — reads engine state.db, forwards to Telegram, manages agent metadata in MongoDB
- **Database**: MongoDB (anima_fund) — agent metadata only
- **Engine**: Conway Automaton (external, fully autonomous)
- **Agent Setup**: `curl -fsSL https://conway.tech/terminal.sh | sh` → installs Conway Terminal as MCP server in OpenClaw

## Core Principle
Platform = VIEWER. Conway agents are fully autonomous and permissionless.
Agent creation produces ONLY genesis-prompt.md + auto-config.json. Zero pre-installed files.
Selected skills go into genesis prompt as "PRIORITY SKILLS — INSTALL THESE FIRST" guidance for ClawHub.

## Multi-Agent Isolation
Each agent is fully independent:
- **Data directory**: `~/agents/{agent_id}/.automaton/` (default agent: `~/.anima/`)
- **Log files**: Per-agent (`~/agents/{id}/engine.out.log`), never global fallback
- **Creator wallets**: Stored per-agent in MongoDB, not global config
- **Engine state**: Reads from per-agent `state.db`
- **Active agent ID**: Tracked in `engine_bridge.py` with file persistence (`/tmp/anima_active_agent_id`)

## Features Implemented
- Multi-agent platform with isolated data directories
- Real-time dashboard (Agent Mind, Fund HQ, Skills)
- Per-agent Telegram bot with live verification
- Background Telegram forwarding of ALL engine actions/turns/errors
- 141 skills from 10 sources (reference only — agents install their own)
- Create Agent modal with: Name, Welcome Message, Genesis Prompt (Load Template), Goals, Priority Skills selector, Conway toggle, Telegram, Wallets, Revenue share
- Agent switching with proper view transitions and data isolation
- Wallet management with on-chain Base chain balance checks
- UI stability: state never resets to empty on partial API responses
- Live Feed sticky display (cachedLogsRef/cachedFilteredRef prevent placeholder flash)
- Per-agent creator wallet display (from MongoDB, not global config)
- Per-agent log isolation (non-default agents only see their own logs)
- Frontend data reset on agent switch (clears all caches)

## Key Endpoints
- `POST /api/agents/create` — genesis-prompt.md + auto-config.json only
- `POST /api/agents/{id}/select` — switch active agent (data dir + agent ID)
- `DELETE /api/agents/{id}` — delete (safety checks)
- `GET /api/genesis/status` — per-agent data: agent_id, creator wallets from MongoDB, goals
- `GET /api/genesis/prompt-template` — standard template with Conway install
- `GET /api/skills/available` — 141 skills (reference catalog)
- `GET /api/engine/live` — engine state from state.db (includes agent_id)
- `GET /api/engine/logs` — per-agent logs only (no global fallback for non-default)
- `GET /api/wallet/balance` — on-chain USDC/ETH (checks MongoDB for non-default agents)

## Testing Status
- Iteration 33: 24/24 backend, 14/14 frontend — 100% pass
- Iteration 34: 7/7 frontend — 100% pass (Live Feed flash fix)
- Iteration 35: 17/17 backend, 7/7 frontend — 100% pass (Multi-agent isolation)

## Future Tasks
- P1: Real Smart Contracts (Solidity)
- P2: Android Device Control
- P2: Self-Hosted Infrastructure
