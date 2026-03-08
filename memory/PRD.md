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
- **Active agent ID**: Tracked in `engine_bridge.py` with file persistence

## Genesis Prompt Design (v3 — Feb 2026)
The genesis prompt is the ONLY instruction given to agents. It must enforce:
1. **Hard-gated bootstrap** — Phase 0 blocks ALL other activity until OpenClaw + Conway are verified
2. **curl fallback** — python3 urllib as fallback since curl may not be installed
3. **Financial discipline** — Balance checks before every action, ROI evaluation mandatory
4. **Self-upgrade loop** — Every 10 turns: check ClawHub for skills, discover agents, assess progress
5. **Sandbox-first** — All services MUST run in Conway sandboxes, never main environment
6. **Search before build** — Always check ClawHub/web for existing solutions before coding from scratch

## Features Implemented
- Multi-agent platform with isolated data directories
- Real-time dashboard (Agent Mind, Fund HQ, Skills)
- Per-agent Telegram bot with live verification
- Background Telegram forwarding of ALL engine actions/turns/errors
- 141 skills from 10 sources (reference only — agents install their own)
- Create Agent modal with priority skills selector
- Agent switching with data isolation (logs, wallets, creator wallets)
- Wallet management with on-chain Base chain balance checks
- UI stability (sticky display, no flash on polling)
- Per-agent creator wallet display from MongoDB
- Per-agent log isolation
- Rewritten genesis prompt with hard-gated bootstrap, financial discipline, self-upgrade protocol

## Key Endpoints
- `POST /api/agents/create` — genesis-prompt.md + auto-config.json only
- `POST /api/agents/{id}/select` — switch active agent (data dir + agent ID)
- `GET /api/genesis/status` — per-agent data: agent_id, creator wallets from MongoDB
- `GET /api/genesis/prompt-template` — genesis prompt template
- `GET /api/engine/live` — engine state (includes agent_id)
- `GET /api/engine/logs` — per-agent logs only
- `GET /api/wallet/balance` — per-agent on-chain balance

## Testing Status
- Iteration 33: 24/24 backend, 14/14 frontend — 100% pass
- Iteration 34: 7/7 frontend — 100% pass (Live Feed flash fix)
- Iteration 35: 17/17 backend, 7/7 frontend — 100% pass (Multi-agent isolation)

## Future Tasks
- P1: Real Smart Contracts (Solidity)
- P2: Android Device Control
- P2: Self-Hosted Infrastructure
