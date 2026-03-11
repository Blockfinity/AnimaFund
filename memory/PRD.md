# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed Conway Cloud VM on the live internet.

## Core Architecture
- **Backend:** FastAPI + MongoDB + Conway Cloud API integration
- **Frontend:** React with SSE-driven real-time data
- **Data Pipeline:** Hybrid (webhook instant push + unified background poller)
- **SSE:** Single EventSource via React Context (`SSEProvider`) — single source of truth
- **Key Storage:** Conway API key stored PER-AGENT (provisioning-status.json + MongoDB agent doc)
- **Security:** Agent has ZERO access to host. All operations inside sandbox only.

## Navigation Flow
- **Genesis screen** — standalone provisioning screen
  - Agent selector bar (all created agents + "Create" button)
  - Conway Account (API key input, editable on click)
  - VM tier selector (5 Conway tiers)
  - 6-step provisioning stepper
  - "Go to Dashboard" button
- **Dashboard** — full agent monitoring/management
  - Header: Genesis pill + Wallet pill + LIVE indicator + Agent dropdown
  - Sidebar: 13 pages
- **Create Agent modal** — collects config → "Genesis" button → redirects to genesis for provisioning

## Phase 0: Tool Verification
After all tools are installed (step 6), the agent runs `phase0-verify.py` which USES each tool:
1. Conway Terminal — checks binary + version
2. Wallet — verifies address + API key from ~/.conway/config.json
3. OpenClaw — verifies binary + MCP config
4. Claude Code — verifies binary + MCP registration
5. File I/O — write + read + delete test
6. Network — outbound HTTPS to api.conway.tech
7. Credits API — checks balance using wallet API key
8. Skills — verifies skills directory has files

Results stored in phase-state.json. Phase 0 only completes when ALL tools pass.

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
- [x] Per-agent Conway API key storage
- [x] Conway API key input with validation and edit-on-click
- [x] VM tier selector (5 Conway tiers)
- [x] Server startup auto-restore keys from MongoDB
- [x] Genesis ↔ Dashboard navigation (pills in header + buttons)
- [x] Genesis agent list with Create button
- [x] Create Agent modal → "Genesis" → provisioning
- [x] Phase 0 tool verification script (uses each tool, not just API calls)
- [x] /api/provision/verify-tools endpoint for on-demand verification
- [x] Deployment readiness confirmed by deployment agent
- [x] Deployment prep: removed hardcoded preview URL, fixed stale module-level API key in genesis.py

## P0: Active Blockers
- User verification pending: Conway API key edit + credit balance refresh UI

## P1: Upcoming
- Security refactor: deploy-agent reads secrets from host env vars (lines 1537-1542, 1778-1783 of agent_setup.py) — must read from MongoDB agent doc instead
- Wire step 6 to read agent config from MongoDB (not host env vars)
- Restructure provisioning steps to match Conway's actual flow
- Implement Real Smart Contracts

## P2: Future/Backlog
- Multiple VMs per agent
- Android device control integration
- Self-hosted agent engine migration
