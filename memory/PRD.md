# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform where independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via the Conway ecosystem.

## Architecture
- **Frontend**: React (port 3000) with shadcn/ui, 11 pages
- **Backend**: FastAPI (port 8001) with MongoDB, 7 routers
- **Agent Engine**: Automaton TypeScript runtime (`dist/bundle.mjs`) with SQLite state.db
- **Conway Integration**: Conway Terminal MCP v2.0.9 + native Conway API client
- **External Services**: Conway Cloud, Conway Compute, Conway Domains, Telegram Bot API, x402 payments

## Conway Ecosystem — FULL Integration Status

### Conway Terminal (MCP Server) — v2.0.9
- **Installed**: `/usr/bin/conway-terminal`
- **Wallet**: `~/.conway/wallet.json` (EVM private key, shared identity)
- **Config**: `~/.conway/config.json` (API key `cnwy_k_...`)
- **Skills shipped with npm package**:
  - `conway-automaton/SKILL.md` → installed to `~/.anima/skills/conway-automaton/`
  - `conway-openclaw/SKILL.md` → installed to `~/.openclaw/skills/conway/`
- **Commands shipped with npm package**:
  - `/conway` (status, deploy, domains, fund, setup, help)
  - `/conway-deploy` (guided deployment workflow)
  - `/conway-status` (wallet + credits + sandboxes quick view)
  - All installed to `~/.anima/commands/`
- **36 MCP tools**: sandbox (8), PTY (5), inference (1), domains (13), credits (3), x402 (5)
- **Modes**: stdio (default, for agent connection) + HTTP (for testing)

### Conway Cloud (api.conway.tech) — HEALTHY
- Sandboxes: Create, list, delete Linux VMs (Firecracker microVMs, Ubuntu 22.04)
- Execution: Run commands and code in sandboxes
- Files: Upload, download, list files in sandboxes
- Ports: Expose ports → public URLs at `{port}-{sandbox_id}.life.conway.tech`
- PTY Sessions: Interactive terminal sessions (create, write, read, close, list)
- Web Terminal: Browser-based sandbox access
- Regions: eu-north, us-east

### Conway Compute (inference.conway.tech) — HEALTHY
- OpenAI-compatible Chat Completions API
- Models: gpt-5.2/5.3, claude-opus-4.6, claude-sonnet-4.5, gemini-2.5-pro, kimi-k2.5, qwen3-coder
- Streaming SSE support
- Billed from Conway credits

### Conway Domains (api.conway.domains) — HEALTHY
- Domain search, check, registration, renewal
- DNS management (full CRUD)
- SIWE/SIWS wallet authentication
- Privacy protection (WHOIS)
- Nameserver management
- x402 USDC payments for registration

### x402 Payments
- USDC on Base (EVM) or Solana
- EIP-3009 `transferWithAuthorization` for gasless payments
- Built into Conway Terminal — automatic payment handling
- wallet_info, wallet_networks, x402_discover, x402_check, x402_fetch tools

### Automatons (Identity Registration)
- POST /v1/automatons/register with EIP-712 signed payload
- Immutable fields: automaton_address, creator_address, name, bio, genesis_prompt_hash

### OpenClaw MCP Configuration
- Config file: `~/.openclaw/openclaw.json` (correct filename per terminal.sh)
- Conway MCP server configured with API key
- Conway OpenClaw skill installed at `~/.openclaw/skills/conway/SKILL.md`

### Automaton Installer Flow (conway.tech/automaton.sh)
15-step flow: preflight → install runtime → setup → wallet → provision → funding → config → heartbeat → git → SOUL.md → skills → ERC-8004 → database → systemd → wake up

## Backend API Endpoints

### Conway Router (`/api/conway/*`)
| Endpoint | Description |
|---|---|
| `GET /api/conway/balance` | Real-time credits + sandbox count from Conway API |
| `GET /api/conway/health` | Health of all 3 Conway services |
| `GET /api/conway/sandboxes` | List sandboxes from Conway Cloud |
| `GET /api/conway/credits/pricing` | VM and credit pricing tiers |
| `GET /api/conway/credits/history` | Credit transaction history |
| `GET /api/conway/domains/search` | Public domain search |
| `GET /api/conway/inference/health` | Inference API status |

### Other Routers
- `agents.py` — Multi-agent CRUD, 141 skills across 10 sources
- `genesis.py` — Agent creation/reset, status, prompt template, Conway balance
- `live.py` — 25+ endpoints reading from state.db
- `infrastructure.py` — Sandbox/domain/terminal data from tool_calls
- `telegram.py` — Telegram bot health/config

## Frontend (11 Pages)
Agent Mind (3 tabs), Fund HQ, Agents, Infrastructure (6 tabs), Skills (filters + search), Deal Flow, Portfolio, Financials, Activity, Memory, Configuration

## Per-Agent Data Flow (FIXED)

All 11 frontend pages now receive `selectedAgent` prop from App.js and include it in their `useEffect` dependency arrays. This ensures:
- Immediate re-fetch when switching between agents (no stale data)
- Each page displays the correct agent's data from state.db
- Backend `engine_bridge.py` reads from `_active_data_dir` which switches per `POST /api/agents/{id}/select`

### Pages with selectedAgent:
AgentMind, FundHQ, Infrastructure, Skills, DealFlow, Portfolio, Financials, Activity, Memory, Configuration

### Multi-Agent Data Isolation:
- Each agent: `~/agents/{id}/` with `.anima/` (state.db, skills, config)
- Default agent (anima-fund): `~/.anima/` at root
- Agent creation: `POST /api/agents/create` → isolated HOME dir + bootstrap
- Agent switching: `POST /api/agents/{id}/select` → updates `_active_data_dir` globally
- Agent deletion: `DELETE /api/agents/{id}` → removes from MongoDB + filesystem

## Per-Agent Sandboxing (IMPLEMENTED)

### Isolation Architecture
- **Each agent gets**: `~/agents/{agent_id}/` as isolated HOME directory
- **Conway self-provisioning**: Agents create their OWN wallet + API key on first engine run (platform does NOT copy its global credentials)
- **OpenClaw MCP config**: Per-agent at `~/agents/{id}/.openclaw/openclaw.json` with empty `env{}` — agent provides own Conway API key at runtime
- **File permissions**: All agent dirs set to `chmod 700` (owner-only)
- **Environment sanitization**: Platform strips `MONGO_URL`, `DB_NAME`, `DASHBOARD_URL` from agent process env before launch
- **Conway sandbox isolation**: Each agent operates in its own Conway Cloud sandbox VM (when funded). `sandboxId` in identity → `isLocal=false` → all exec/file operations go to remote VM, not host

### What the platform controls vs what agents control
| Responsibility | Owner |
|---|---|
| Agent HOME directory | Platform creates `~/agents/{id}/` |
| Conway wallet + API key | Agent self-provisions on first run |
| Conway sandbox VM | Agent creates via Conway Cloud API (when funded) |
| Genesis prompt + config | Platform writes to agent's dir |
| Skills + commands | Platform pre-installs from Conway Terminal npm |
| File permissions | Platform sets chmod 700 |
| Environment secrets | Platform strips before passing to agent |

## Current State (as of this session)
- **Conway Terminal**: v2.0.9 installed, provisioned, skills & commands installed
- **Conway APIs**: All 3 healthy and accessible
- **Credits**: $0.00 (CRITICAL tier) — wallet needs funding
- **Agent**: Sleeping (0 credits, stuck in loop — unrecoverable)
- **Engine**: Not running
- **Testing**: 42 iterations, latest: 16/16 backend + 100% frontend PASS
- **Deployment**: Verified ready, no blockers

## What's Been Implemented
- [x] Full multi-agent dashboard with real-time data from state.db
- [x] Conway Terminal v2.0.9 installed and provisioned with wallet + API key
- [x] Conway API router (7 endpoints) querying all 3 Conway services
- [x] OpenClaw MCP config with correct filename (openclaw.json)
- [x] Conway skills from npm package installed (conway-automaton + conway-openclaw)
- [x] Conway commands installed (conway, conway-deploy, conway-status)
- [x] Bootstrap script with full 7-step setup (dirs, terminal, provision, sync, openclaw, skills, verify)
- [x] 100 skills in ~/.anima/skills/ including conway-automaton, conway-compute, conway-payments, survival
- [x] Wallet balance with on-chain USDC/ETH + Conway credits
- [x] Skills catalog: 141 skills (Conway Cloud/Compute/Domains/x402/Credits, OpenClaw, ClawHub, Engine, Anima)
- [x] Infrastructure dashboard (6 tabs: Overview, Sandboxes, Terminal, Domains, Tools, Network)
- [x] Telegram bot integration for agent communication
- [x] Genesis prompt with anti-loop rules, Conway tool guidance, parallel execution strategy
- [x] Dead code cleanup (telegram_logs.py removed)

## Next Steps (P0)
- Fund Conway wallet with USDC on Base (send to 0x700e6b8f41551Cd6162C63047a4556fF35Eb9B07)
- Or buy credits at app.conway.tech
- Create NEW agent with improved genesis prompt
- Verify agent operates correctly via dashboard

## Future/Backlog
- Real smart contracts integration
- Android device control
- Self-hosted agent engine migration
- Revenue tracking charts
- Multi-agent communication dashboard
- Historical analysis of agent turns/costs
