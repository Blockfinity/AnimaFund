# Anima Fund - PRD

## Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform ("Anima Fund"). A multi-agent platform where independent AI agents can be created, monitored, and managed from a single dashboard. Each agent has its own goals, skills, wallets, revenue model, and dedicated Telegram bot.

## Architecture
- **Frontend**: React (port 3000) with Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI (port 8001) with MongoDB
- **Database**: MongoDB (anima_fund)
- **Engine**: Conway Research Automaton (external)
- **Integrations**: Telegram Bot API, Base blockchain (USDC), OpenClaw, ClawHub

## Core Features (All Implemented)
- Multi-agent platform with isolated data directories
- Real-time dashboard (Agent Mind, Fund HQ)
- Per-agent Telegram bot configuration with live verification
- 141 skills from 9 sources (Anima, Conway, OpenClaw, ClawHub, MCP, Engine)
- Conway tools integration (optional per agent)
- Wallet management with on-chain balance checks
- Agent creation modal with Telegram verification
- Telegram Health Dashboard
- Fund deletion safety (wallet protection)
- Auto-scroll mechanism (non-intrusive, ref-based)

## Key Endpoints
- `GET /api/health` - Health check
- `GET /api/agents` - List agents
- `POST /api/agents/create` - Create agent (requires Telegram creds)
- `DELETE /api/agents/{agent_id}` - Delete agent (with safety checks)
- `PUT /api/agents/{agent_id}/telegram` - Update Telegram config
- `GET /api/genesis/status` - Genesis agent status
- `GET /api/skills/available` - All skills (141)
- `GET /api/telegram/health` - Bot health dashboard
- `GET /api/wallet/balance` - On-chain balance

## Current State (March 8, 2026)
- **Status**: Deployment-ready
- **Active Agents**: 1 (Anima Fund - default)
- **Test Data**: All test agents cleaned
- **Testing**: E2E passed (iteration 31) - 30/30 backend, 16/16 frontend

## Future Tasks (Backlog)
- P1: Implement Real Smart Contracts (Solidity)
- P2: Android Device Control Integration
- P2: Self-Hosted Infrastructure Migration
