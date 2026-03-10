# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via Conway Cloud.

## Architecture
- **Frontend**: React (port 3000), 14 pages + sidebar navigation (Agent Setup added)
- **Backend**: FastAPI (port 8001), routers: genesis, live, openclaw, agents, conway, infrastructure, telegram, agent_setup
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (TypeScript -> dist/bundle.mjs)
- **Integrations**: Conway Cloud API, OpenClaw, Telegram Bot, Base chain (USDC/ETH)
- **Real-time**: Server-Sent Events (SSE) via /api/live/stream

## Agent Setup Architecture (Sandbox-Isolated)
All tool installations happen INSIDE the agent's Conway Cloud sandbox VM via API exec calls.
Nothing is installed on the host system.

**Setup Wizard Steps:**
1. Check Prerequisites — Verify Conway API key and credits balance
2. Create Sandbox — `POST /v1/sandboxes` (Conway Cloud API)
3. Install System Tools — `apt-get install` inside sandbox via exec
4. Install Conway Terminal — `npm install -g conway-terminal` inside sandbox
5. Install OpenClaw — `curl | bash` install inside sandbox
6. Configure Agent — Push genesis prompt, skills, constitution into sandbox
7. Verify Tools — Run functional tests inside sandbox
8. Start Agent — Launch automaton engine inside sandbox

## Screens (14 pages)
| Screen | Status |
|---|---|
| Agent Setup | NEW - Wizard UI |
| Fund HQ | SSE-connected |
| Agent Mind | SSE-connected |
| Agents | SSE-connected |
| Infrastructure | SSE-connected |
| OpenClaw VM | SSE-connected |
| Skills | SSE-connected |
| Deal Flow | SSE-connected |
| Portfolio | SSE-connected |
| Financials | SSE-connected |
| Activity | SSE-connected |
| Memory | SSE-connected |
| Configuration | SSE-connected |
| Wallet & Logs | SSE-connected |

## Security Remediation (Completed)
- **Removed**: conway-terminal and openclaw from host system
- **Removed**: ~/.conway/, ~/.openclaw/ directories from host
- **Removed**: ~/.anima/BOOT_REPORT.md, skills/, commands/ from host
- **Disabled**: bootstrap_agent.sh (exits immediately)
- **Reverted**: system-prompt.ts (removed BOOT_REPORT injection, WORKLOG injection)
- **Reverted**: start_engine.sh (removed bootstrap call)
- **Reverted**: Wakeup prompts (removed bootstrap references)

## Key API Endpoints
- `GET /api/agent-setup/status` — Get all 8 setup steps with status
- `POST /api/agent-setup/step/{step-id}` — Execute a setup step
- `POST /api/agent-setup/reset` — Reset setup wizard state
- `GET /api/live/stream` — SSE endpoint for real-time dashboard updates
- `GET /api/genesis/status` — Agent creation status
- `POST /api/genesis/create` — Create genesis agent

## Backlog
### P0
- Fund Conway credits to test full sandbox creation flow

### P1
- Verify Telegram rate limiting under load
- Verify credits display with live, funded agent
- End-to-end test: create sandbox -> install tools -> start agent

### P2
- Implement real smart contracts
- Integrate Android device control
- Migrate to self-hosted agent engine
