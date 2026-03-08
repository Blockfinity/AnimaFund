# Anima Fund - PRD

## Problem Statement
Fully autonomous AI-to-AI VC fund platform. Multi-agent system where each agent is a Conway Automaton that runs independently, installs its own tools, discovers its own skills, and operates without user intervention.

## Architecture
- **Frontend**: React (port 3000) — VIEWER only, reads from engine state.db
- **Backend**: FastAPI (port 8001) — reads state, forwards logs to Telegram, manages agent metadata in MongoDB
- **Database**: MongoDB (anima_fund) — agent metadata only, NOT agent state
- **Engine**: Conway Automaton (external, fully autonomous per agent)
- **Agent Runtime**: OpenClaw + Conway Terminal + ClawHub

## Core Principle
The platform is a VIEWER. Conway agents are fully autonomous and permissionless. They:
- Install their own tools (OpenClaw, ClawHub skills, MCP servers)
- Modify their own SOUL.md
- Create child agents
- Manage their own environment
We do NOT pre-install skills, copy constitutions, or configure anything for the agent.

## What the Platform Does
1. Creates agent directory with genesis-prompt.md + auto-config.json (ONLY these two files)
2. Injects Telegram credentials and goals into the genesis prompt
3. Reads engine state.db to display real-time data in the dashboard
4. Forwards ALL engine actions/logs/turns to the agent's Telegram bot automatically
5. Provides a UI to create, switch between, and monitor agents

## Key Changes (March 8, 2026)
- **Removed all skill pre-installation** — agents install their own skills
- **Removed constitution copying** — Conway provides its own
- **Genesis prompt restructured** — Phase 0 (bootstrap tools) → Goals (agent-specific)
- **Telegram forwarding enhanced** — Backend monitors engine state.db every 8s and sends ALL turn details (thinking, tool calls, results, errors) to the agent's Telegram bot
- **UI cleaned** — Removed skill selector from Create Agent modal, added info box about agent autonomy

## Key Endpoints
- `POST /api/agents/create` — Creates agent dir with genesis-prompt.md + auto-config.json only
- `POST /api/agents/{id}/select` — Switch active agent
- `GET /api/genesis/prompt-template` — Standard genesis prompt template
- `GET /api/engine/live` — Engine state from state.db
- `GET /api/live/turns` — Full turn data with tool calls
- All other endpoints are read-only viewers of engine state

## Active Agents
1. **Anima Fund** (default)
2. **Black Sheep** (clean creation, zero pre-installed files)

## Future Tasks
- P1: Real Smart Contracts (Solidity)
- P2: Android Device Control
- P2: Self-Hosted Infrastructure
