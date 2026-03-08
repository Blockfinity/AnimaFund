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

## Features Implemented
- Multi-agent platform with isolated data directories
- Real-time dashboard (Agent Mind, Fund HQ, Skills)
- Per-agent Telegram bot with live verification
- Background Telegram forwarding of ALL engine actions/turns/errors
- 141 skills from 10 sources (reference only — agents install their own)
- Create Agent modal with: Name, Welcome Message, Genesis Prompt (Load Template), Goals, Priority Skills selector, Conway toggle, Telegram, Wallets, Revenue share
- Agent switching with proper view transitions
- Wallet management with on-chain Base chain balance checks
- UI stability: state never resets to empty on partial API responses

## Key Endpoints
- `POST /api/agents/create` — genesis-prompt.md + auto-config.json only
- `POST /api/agents/{id}/select` — switch active agent
- `DELETE /api/agents/{id}` — delete (safety checks)
- `GET /api/genesis/status` — includes creator_eth_address, creator_wallet
- `GET /api/genesis/prompt-template` — standard template with Conway install
- `GET /api/skills/available` — 141 skills (reference catalog)
- `GET /api/engine/live` — engine state from state.db
- `GET /api/wallet/balance` — on-chain USDC/ETH

## Testing Status
- Iteration 33: 24/24 backend, 14/14 frontend — 100% pass
- Deployment agent: passed (hardcoded ETH address fixed)
- Clean state verified: only default Anima Fund agent

## Future Tasks
- P1: Real Smart Contracts (Solidity)
- P2: Android Device Control
- P2: Self-Hosted Infrastructure
