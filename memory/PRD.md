# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via Conway Cloud.

## Architecture
- **Frontend**: React (port 3000), 13 pages + sidebar navigation
- **Backend**: FastAPI (port 8001), 7 routers (agents, genesis, live, telegram, infrastructure, conway, openclaw)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (TypeScript, compiled to dist/bundle.mjs)
- **Integrations**: Conway Cloud API, OpenClaw, Telegram Bot, Base chain (USDC/ETH)

## Two Genesis Prompt System
1. **Anima Fund (The Catalyst)**: `/root/.anima/genesis-prompt.md` — VC fund founder with specific identity and fund model
2. **Generic Agent Template**: `/app/automaton/genesis-prompt.md` — For new agents via CreateAgentModal
3. **Both include identical mandatory boot sequence** (Steps 0-7)
4. **Push-genesis skips anima-fund** to protect The Catalyst's custom prompt

## All Screens & Connections (13 pages)
| Screen | Page | Backend APIs | Status |
|---|---|---|---|
| Agent Mind | AgentMind.js | /api/engine/live, /api/live/*, /api/wallet/balance | VERIFIED |
| Fund HQ | FundHQ.js | /api/engine/live, /api/live/*, /api/telegram/health | VERIFIED |
| Agents | Agents.js | /api/live/agents, /api/live/discovered | VERIFIED (prop fix) |
| Infrastructure | Infrastructure.js | /api/infrastructure/* | VERIFIED |
| **OpenClaw VM** | **OpenClawViewer.js** | **/api/openclaw/** | **NEW** |
| Skills | Skills.js | /api/live/skills-full, /api/skills/available | VERIFIED |
| Deal Flow | DealFlow.js | /api/live/memory | VERIFIED |
| Portfolio | Portfolio.js | /api/live/memory | VERIFIED |
| Financials | Financials.js | /api/live/financials, /api/live/transactions | VERIFIED |
| Activity | Activity.js | /api/infrastructure/activity-feed | VERIFIED |
| Memory | Memory.js | /api/live/memory, /api/live/kv | VERIFIED |
| Configuration | Configuration.js | /api/constitution, /api/engine/status | VERIFIED |
| Wallet & Logs | AgentMind.js | same as Agent Mind | VERIFIED |

## New: OpenClaw VM Viewer
- 4 tabs: Live View, Actions, Sandbox VMs, Browsing
- Real-time auto-refresh every 5 seconds
- Shows browsing sessions (browse_page calls), sandbox VMs (Conway API), all agent tool calls
- Empty state messaging when agent is idle
- Filter by action category (browsing, sandbox, payment, network, tools)

## Test Results
- **Unit tests**: 21/21 passed at `/app/backend/tests/test_api.py`
- **E2E iteration 47**: 18/19 backend + 100% frontend (all 12 feature categories verified)
- **Deployment check**: PASS

## Remaining Tasks

### P0 (Critical)
- Start the agent engine and monitor first 10 turns

### P1 (High)
- Verify Telegram messages, skills loading, wallet updates during live operation
- OpenClaw data populates once agent starts using browse_page/sandbox tools

### P2 (Medium)
- Real smart contracts (ERC-8004)
- Android device control
- Self-hosted agent engine
- Revenue tracking charts
- Multi-agent communication dashboard

### Backlog
- Domain trading automation, agent marketplace, cross-chain wallets, performance scoring
