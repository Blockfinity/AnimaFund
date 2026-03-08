# Anima Fund - PRD

## Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform ("Anima Fund"). A multi-agent platform where independent AI agents can be created, monitored, and managed from a single dashboard.

## Architecture
- **Frontend**: React (port 3000) with Tailwind CSS
- **Backend**: FastAPI (port 8001) with MongoDB
- **Database**: MongoDB (anima_fund)
- **Engine**: Conway Research Automaton (external)

## Core Features (All Implemented)
- Multi-agent platform with isolated data directories
- Real-time dashboard (Agent Mind, Fund HQ)
- Per-agent Telegram bot configuration with live verification
- 141 skills from 9 sources
- Conway tools integration (optional per agent)
- Wallet management with on-chain balance checks
- Agent creation modal with Telegram verification + "Load Standard Template" button
- Telegram Health Dashboard
- Fund deletion safety (wallet protection)
- Agent switching with proper view transitions

## Critical Fixes (March 8, 2026)

### Genesis Prompt Rewrite (MAJOR)
**Problem**: Agents were skipping tool setup (OpenClaw, Conway, ClawHub), not using Telegram, getting stuck in loops, and jumping to revenue strategies they couldn't execute without tools.

**Solution**: Complete restructure of genesis-prompt.md:
- **Phase 0: MANDATORY BOOTSTRAP** — Install and verify Conway Terminal, OpenClaw, ClawHub skills, Telegram — LOCKED until all pass
- **Phase 1: TOOL VERIFICATION** — Real tests of each tool with Telegram reporting
- **Phase 2: REVENUE OPERATIONS** — Only after Phases 0+1 complete
- **Anti-Stuck Rules** — 3-turn abandon policy, no repeat failures, strategy pivoting
- **Telegram EVERY TURN** — Python3 urllib method (zero dependencies, always works), explicit code blocks agents copy directly

### Skill Updates
- `telegram-reporting/SKILL.md` — Rewritten to use ONLY the python3 urllib method that always works. Explicitly warns against unreliable methods (send_message, curl)
- `openclaw-setup/SKILL.md` — Step-by-step OpenClaw installation, ClawHub skill installation, MCP server setup, verification steps

### Backend Changes
- `{{AGENT_NAME}}` placeholder injection in genesis prompts and skills
- `GET /api/genesis/prompt-template` — New endpoint serving the standard template
- "Load Standard Template" button in Create Agent modal

### UI Flickering Fixes (from earlier)
- SQLite busy_timeout + WAL mode in engine_bridge.py
- Frontend state never resets to empty on partial/failed API responses
- Stable 8s polling, wallet ref persistence, proper agent switching with view reset

## Key Endpoints
- `GET /api/health` - Health check
- `GET /api/agents` - List agents
- `POST /api/agents/create` - Create agent
- `DELETE /api/agents/{agent_id}` - Delete agent
- `POST /api/agents/{agent_id}/select` - Switch active agent
- `GET /api/genesis/status` - Genesis status
- `GET /api/genesis/prompt-template` - Standard genesis prompt template
- `GET /api/skills/available` - All skills (141)
- `GET /api/telegram/health` - Bot health dashboard
- `GET /api/wallet/balance` - On-chain balance

## Active Agents
1. **Anima Fund** (default) — Updated genesis prompt
2. **Black Sheep** — Created with new prompt and verified Telegram (chat_id: 8613975358)

## Future Tasks (Backlog)
- P1: Implement Real Smart Contracts (Solidity)
- P2: Android Device Control Integration
- P2: Self-Hosted Infrastructure Migration
