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
- Agent creation modal with Telegram verification
- Telegram Health Dashboard
- Fund deletion safety (wallet protection)
- Auto-scroll mechanism (non-intrusive, ref-based)
- **Agent switching** with proper view transitions and state reset

## Bug Fixes (March 8, 2026)
### UI Flickering/Data Loss
- Added SQLite busy_timeout=5000 and WAL mode to engine_bridge.py
- Frontend state never resets to empty on partial/failed API responses
- Stable 8s polling interval (replaces cascading adaptive polling)
- Simplified auto-scroll handler (removed debounce conflicts)
- Ref-backed wallet address persistence

### Agent Switching
- View resets to 'loading' on agent switch for proper re-evaluation
- Genesis screen shows correct agent name (not hardcoded "ANIMA FUND")
- Agent switcher buttons on genesis screen for navigation
- walletAddrRef clears on agent switch to prevent stale data
- Backend error handling on select (404 re-fetches agent list)
- handleAgentCreated fetches fresh agent list from backend

## Key Endpoints
- `GET /api/health` - Health check
- `GET /api/agents` - List agents
- `POST /api/agents/create` - Create agent
- `DELETE /api/agents/{agent_id}` - Delete agent (with safety)
- `POST /api/agents/{agent_id}/select` - Switch active agent
- `GET /api/genesis/status` - Genesis status (agent-aware)
- `GET /api/skills/available` - All skills (141)
- `GET /api/telegram/health` - Bot health dashboard
- `GET /api/wallet/balance` - On-chain balance

## Current State
- **Active Agents**: 2 (Anima Fund, Black Sheep)
- **Testing**: E2E passed iterations 31-32, manual screenshot verification for switching

## Future Tasks (Backlog)
- P1: Implement Real Smart Contracts (Solidity)
- P2: Android Device Control Integration
- P2: Self-Hosted Infrastructure Migration
