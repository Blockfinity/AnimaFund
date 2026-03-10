# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed Conway Cloud VM on the live internet.

## Core Architecture
- **Backend:** FastAPI + MongoDB + Conway Cloud API integration
- **Frontend:** React with SSE-driven real-time data
- **Data Pipeline:** Hybrid (webhook instant push + unified background poller)
- **SSE:** Single EventSource via React Context (`SSEProvider`) — single source of truth
- **Key Storage:** Conway API key stored PER-AGENT (provisioning-status.json + MongoDB agent doc)

## Navigation Flow
- **Genesis screen** — standalone provisioning screen, always accessible
  - Agent selector bar (all agents + "Create" button)
  - Conway Account (API key input, editable on click)
  - VM tier selector (5 Conway tiers)
  - 6-step provisioning stepper
  - After step 6 → wallet/funding screen
  - "Go to Dashboard" button
- **Dashboard** — full agent monitoring/management
  - Header: Genesis pill + Wallet pill + LIVE indicator + Agent dropdown
  - Sidebar: 13 pages (Anima VM, Agent Mind, Fund HQ, etc.)
- **Create Agent modal** — collects name/prompt/goals/skills → "Genesis" button → redirects to genesis for provisioning

## Per-Agent Data Isolation
Each agent has its own:
- `provisioning-status.json` with `conway_api_key` field
- MongoDB document with `conway_api_key` field
- Sandbox/VM on Conway Cloud (1 agent per VM)
- When switching agents: poller, SSE, and all Conway API calls scope to that agent

## Conway VM Tiers
| Tier | vCPU | RAM | Disk | Price |
|------|------|-----|------|-------|
| Small | 1 | 512MB | 5GB | $5/mo |
| Medium | 1 | 1GB | 10GB | $8/mo |
| Large | 2 | 2GB | 20GB | $15/mo |
| X-Large | 2 | 4GB | 40GB | $25/mo |
| 2X-Large | 4 | 8GB | 80GB | $45/mo |

## What's Been Implemented
- [x] Full SSE data pipeline (webhook + poller → SSE → React Context)
- [x] Complete frontend audit — all 14 pages use consistent SSE-driven data fetching
- [x] Per-agent Conway API key storage (provisioning-status.json + MongoDB)
- [x] Conway API key input with validation and edit-on-click
- [x] VM tier selector (5 Conway tiers)
- [x] Server startup auto-restore keys from MongoDB
- [x] Agent switching loads correct key and scopes data
- [x] Genesis ↔ Dashboard navigation (pills in header + buttons)
- [x] Genesis agent list with selectable buttons + "Create" button
- [x] Create Agent modal → "Genesis" button → redirects to genesis for provisioning
- [x] Credit purchase audit trail (MongoDB)
- [x] Deployment readiness (env var fallbacks)

## P1: Upcoming
- Implement Real Smart Contracts
- Create Agent flow: after step 6 auto-redirect to wallet screen

## P2: Future/Backlog
- Multiple VMs per agent (agent can spin up additional VMs)
- Android device control integration
- Self-hosted agent engine migration
