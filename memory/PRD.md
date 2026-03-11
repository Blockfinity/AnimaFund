# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed Conway Cloud VM on the live internet.

## Architecture: Platform vs Agents
- **PLATFORM** = React frontend + FastAPI backend + MongoDB. Standard web app deployed normally. Monitors and manages agents remotely.
- **AGENTS** = Autonomous AIs built on Automaton. Each runs inside its own Conway Cloud VM for isolation and autonomy.
- The platform CREATES and MONITORS agents but does NOT run agent logic itself.

## Two Prompts
1. **AI VC Fund Prompt (System Prompt)** — Pre-loaded for the default "anima-fund" founder agent. No creation wizard needed — just provision a Conway VM and deploy.
2. **Genesis Prompt** — Template used when creating additional agents (GPs, analysts, etc.) through the Create Agent flow.

## Core Architecture
- **Backend:** FastAPI + MongoDB (single source of truth for all state)
- **Frontend:** React with SSE-driven real-time data
- **State Management:** `agent_state.py` centralizes all MongoDB access
- **Data Pipeline:** Hybrid (webhook instant push + unified background poller)
- **SSE:** Single EventSource via React Context (`SSEProvider`)
- **Key Storage:** Conway API key per-agent in MongoDB
- **Security:** Platform never accesses host filesystem for state. Agents run in Conway VMs only.

## What's Been Implemented
- [x] Full SSE data pipeline (webhook + poller → SSE → React Context)
- [x] Complete frontend audit — all 14 pages use consistent SSE-driven data fetching
- [x] Per-agent Conway API key storage in MongoDB
- [x] Conway API key input with validation and edit-on-click
- [x] VM tier selector (5 Conway tiers)
- [x] Server startup auto-restore keys from MongoDB
- [x] Genesis ↔ Dashboard navigation
- [x] Create Agent modal → MongoDB storage only (no host filesystem)
- [x] Phase 0 tool verification script
- [x] Deployment readiness confirmed
- [x] **MAJOR REFACTOR: Platform-Agent separation enforced**
  - agent_state.py: centralized MongoDB state management
  - All provisioning state migrated from filesystem JSON to MongoDB
  - create_agent() stores in MongoDB only (no host filesystem writes)
  - deploy_agent() reads config from MongoDB agent doc (not host env vars)
  - All API key management through MongoDB
  - 42/42 E2E tests passed post-refactor

## P0: Active Blockers
- User verification pending: Conway API key edit + credit balance refresh with funded key

## P1: Upcoming
- Implement Real Smart Contracts
- Allow agents to purchase/manage multiple VMs

## P2: Future/Backlog
- Android device control integration
- Self-hosted agent engine migration
