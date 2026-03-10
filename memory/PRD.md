# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via Conway Cloud.

## Architecture
- **Frontend**: React (port 3000), 14 pages + sidebar navigation
- **Backend**: FastAPI (port 8001), routers: genesis, live, openclaw, agents, conway, infrastructure, telegram, agent_setup (provision)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (TypeScript -> dist/bundle.mjs)
- **Integrations**: Conway Cloud API, OpenClaw, Telegram Bot, Base chain (USDC/ETH)
- **Real-time**: Server-Sent Events (SSE) via /api/live/stream

## Agent Lifecycle (Live Provisioning)
The agent is **alive from creation**. Provisioning equips a running agent with tools — it's aware of each step.

**Flow:**
1. **Create Agent** → engine starts, agent is born and conscious
2. **Create Sandbox** → button provisions Conway Cloud VM (agent sees: "your creator provisioned a sandbox")
3. **Install Terminal** → conway-terminal installed inside sandbox (agent aware)
4. **Install OpenClaw** → browser agent installed inside sandbox (agent aware)
5. **Load Skills** → skills pushed into sandbox (agent aware)
6. **Go Autonomous / Nudge** → final message: "tools ready, go" → zero human control

**Agent Awareness Mechanism:**
- Each button writes to `~/.anima/provisioning-status.json`
- `system-prompt.ts` Layer 5.5 reads this file and injects it into the agent's context every turn
- Agent naturally sees what tools were installed and can test/use them
- Custom nudge messages also appear in the agent's context

## Key API Endpoints
### Provisioning (prefix: /api/provision)
- `GET /api/provision/status` — current sandbox, tools, skills, nudges, credits
- `POST /api/provision/create-sandbox` — create Conway Cloud VM (X-Large: 2 vCPU, 4GB, 40GB)
- `POST /api/provision/install-terminal` — install conway-terminal inside sandbox
- `POST /api/provision/install-openclaw` — install OpenClaw inside sandbox
- `POST /api/provision/load-skills` — push skills into sandbox
- `POST /api/provision/nudge` — send default autonomy nudge
- `POST /api/provision/nudge/custom` — send custom message to agent
- `POST /api/provision/verify-sandbox` — run tool tests inside sandbox

### Other
- `GET /api/live/stream` — SSE real-time updates
- `GET /api/genesis/status` — agent status
- `POST /api/genesis/create` — create and start agent

## Security
- All tool installations happen INSIDE the agent's sandbox VM via Conway API exec
- Nothing is installed on the host system
- `bootstrap_agent.sh` is disabled (exits immediately)
- `system-prompt.ts` has no BOOT_REPORT references
- Previous host-level installations of conway-terminal and OpenClaw were removed

## Screens (14 pages)
| Screen | Status |
|---|---|
| Provision Agent | NEW - Live provisioning controls |
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

## Backlog
### P0
- Fund Conway credits to test full sandbox creation -> tool installation flow end-to-end

### P1
- Verify Telegram rate limiting under load
- Verify credits display with live, funded agent
- End-to-end test: create sandbox -> install tools -> nudge -> agent uses tools

### P2
- Implement real smart contracts
- Integrate Android device control
- Migrate to self-hosted agent engine
