# Anima Fund - PRD

## Problem Statement
Fully autonomous AI-to-AI VC fund platform. Multi-agent system where each agent is sovereign — installs its own tools, discovers skills, operates freely on the live internet.

## Architecture
- **Frontend**: React (port 3000) — dashboard for agent monitoring
- **Backend**: FastAPI (port 8001) — reads engine state.db, manages agent metadata in MongoDB
- **Database**: MongoDB (anima_fund) — agent metadata only
- **Engine**: External autonomous agent runtime
- **Agent Setup**: Each agent bootstraps itself via genesis prompt

## Core Principle
Platform = VIEWER. Agents are sovereign and fully autonomous.
Agent creation produces ONLY genesis-prompt.md + auto-config.json.
No pre-installed tools. No restrictions on internet access.

## Multi-Agent Isolation
Each agent is fully independent:
- **Data directory**: Per-agent isolated directories
- **Log files**: Per-agent (no global fallback)
- **Creator wallets**: Stored per-agent in MongoDB
- **Engine state**: Per-agent state.db
- **Active agent ID**: Tracked with file persistence

## Genesis Prompt Design (v4 — Feb 2026)
Key principles:
1. **Hard-gated Phase 0** — Nothing happens until OpenClaw + Conway Terminal verified
2. **Full internet freedom** — Agents browse, install, deploy anything
3. **Broad tool discovery** — ClawHub skills, MCP servers (mcp.so, smithery.ai, GitHub), npm, PyPI, GitHub repos, public APIs, other agents
4. **Complete isolation** — Zero traceability to platform. Identity firewall. Clean deployments. Sanitized logs. No platform references in any output.
5. **Sandbox-first** — All services in Conway sandboxes with public URLs
6. **Financial discipline** — Balance checks, ROI evaluation, search-before-build
7. **Continuous self-upgrade** — Every 10 turns: search for new tools, skills, MCPs, collaborators
8. **curl fallback** — python3 urllib as fallback since curl may not be installed

## Features Implemented
- Multi-agent platform with isolated data directories
- Real-time dashboard (Agent Mind, Fund HQ, Skills)
- Per-agent Telegram bot with live verification
- Background Telegram forwarding of all engine activity
- 141 skills catalog (reference only)
- Create Agent modal with priority skills selector
- Agent switching with full data isolation
- Wallet management with on-chain balance checks
- UI stability (sticky display, no flash on polling)
- Per-agent creator wallets from MongoDB
- Per-agent log isolation
- Sovereign genesis prompt with isolation, self-upgrade, and full autonomy

## Key Endpoints
- `POST /api/agents/create` — genesis-prompt.md + auto-config.json
- `POST /api/agents/{id}/select` — switch active agent
- `GET /api/genesis/status` — per-agent data
- `GET /api/genesis/prompt-template` — genesis prompt template
- `GET /api/engine/live` — engine state
- `GET /api/engine/logs` — per-agent logs
- `GET /api/wallet/balance` — per-agent balance

## Testing Status
- Iteration 35: 17/17 backend, 7/7 frontend — 100% pass (Multi-agent isolation)

## Future Tasks
- P1: Real Smart Contracts (Solidity)
- P2: Android Device Control
- P2: Self-Hosted Infrastructure
