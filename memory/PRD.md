# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed Conway Cloud VM on the live internet.

## Core Architecture
- **Backend:** FastAPI + MongoDB + Conway Cloud API integration
- **Frontend:** React with SSE-driven real-time data
- **Data Pipeline:** Hybrid (webhook instant push + unified background poller)
- **SSE:** Single EventSource via React Context (`SSEProvider`) — single source of truth
- **Key Storage:** Conway API key stored PER-AGENT (provisioning-status.json + MongoDB agent doc)

## Per-Agent Data Isolation
Each agent has its own:
- `provisioning-status.json` (file-based, fast sync reads)
- MongoDB document with `conway_api_key` field
- Sandbox/VM on Conway Cloud
- When switching agents: the poller, SSE stream, and all Conway API calls automatically scope to that agent's credentials and sandbox

## Conway API Key Flow
1. User deploys platform → goes to Conway (app.conway.tech) → signs up → gets API key
2. User pastes key in **Conway API Key** panel on genesis screen
3. Key validated against Conway API
4. Stored in: active agent's provisioning-status.json + MongoDB agent doc
5. On redeploy: startup hook restores all agent keys from MongoDB
6. On agent switch: active key switches automatically
7. Same key can be shared across agents OR each agent can have a unique key — user's choice

## Key Technical Decisions
- Conway API key is NOT a global env var — it's per-agent
- `_get_conway_api_key()` in credits.py, sandbox_poller.py, agent_setup.py all read from the ACTIVE agent's provisioning-status.json
- Agent select (`/api/agents/{id}/select`) switches both the active agent ID AND the Conway key
- Sandbox poller reads key dynamically each poll cycle (not at module load)

## What's Been Implemented
- [x] Full SSE data pipeline (webhook + poller → SSE → React Context)
- [x] Complete frontend audit — all 14 pages use consistent SSE-driven data fetching
- [x] Per-agent Conway API key storage (provisioning-status.json + MongoDB)
- [x] Conway API Key input UI on genesis screen with validation
- [x] Server startup auto-restore keys from MongoDB for all agents
- [x] Agent switching loads correct key and scopes data
- [x] Credit purchase audit trail (MongoDB: credit_purchases, credit_verifications)
- [x] Deployment readiness (env var fallbacks for all URLs)
- [x] Auto key-sync from sandbox after install-terminal

## P1: Upcoming
- Implement Real Smart Contracts

## P2: Future/Backlog
- Android device control integration
- Self-hosted agent engine migration
