# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform where new, independent AI agents can be created and managed from a single UI. Each agent must have its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via the Conway Research ecosystem.

## Core Architecture
```
/app
├── automaton/              # Conway engine bundle + genesis prompt template
│   ├── dist/bundle.mjs     # Pre-compiled engine
│   ├── genesis-prompt.md   # LEAN template (~5.8KB, ~100 lines)
│   └── skills/             # 100+ skill definitions
├── backend/
│   ├── server.py           # FastAPI main app (5 routers)
│   ├── engine_bridge.py    # Reads agent data from SQLite state.db
│   ├── config.py           # Shared constants (all from env)
│   ├── database.py         # MongoDB connection
│   └── routers/
│       ├── agents.py       # Agent CRUD, bootstrap, engine start, isolation
│       ├── genesis.py      # Status, logs, wallet balance, prompt template
│       ├── live.py         # Live agent data (turns, soul, identity)
│       ├── infrastructure.py # VM/Sandbox monitoring, terminal, domains, activity feed
│       └── telegram.py     # Telegram notification relay
├── frontend/src/
│   ├── App.js              # Router, stable polling (viewRef pattern)
│   ├── pages/
│   │   ├── AgentMind.js    # Real-time agent monitoring (content-based comparison)
│   │   ├── Infrastructure.js # VM/Sandbox/Domains/Terminal/Tools/Network (6 tabs)
│   │   ├── Activity.js     # Comprehensive activity feed (categorized filters)
│   │   ├── FundHQ.js       # Fund overview
│   │   ├── Agents.js       # Agent list
│   │   └── Skills.js       # Skills browser (141 skills)
│   └── components/
│       ├── Sidebar.js      # Navigation (includes Infrastructure)
│       └── CreateAgentModal.js  # Agent creation with Telegram verification
└── scripts/
    ├── start_engine.sh     # Engine starter (runs bootstrap first)
    └── bootstrap_agent.sh  # Pre-installs Conway Terminal + OpenClaw + syncs to .anima/
```

## Agent Environment Structure (Per Agent)
```
~/agents/{agent_id}/
├── .anima/                 # Primary engine directory
│   ├── wallet.json         # Pre-provisioned wallet (private key)
│   ├── config.json         # Conway API key (cnwy_k_...)
│   ├── auto-config.json    # Non-interactive engine config
│   ├── genesis-prompt.md   # Lean prompt with instructions
│   └── state.db            # Engine SQLite database (created at runtime)
├── .automaton -> .anima    # Symlink for backward compatibility
├── .conway/                # Conway Terminal config
│   ├── wallet.json         # Same wallet (synced from bootstrap)
│   └── config.json         # Same API key
├── .openclaw/              # OpenClaw config
│   └── config.json         # Points to Conway Terminal MCP server
├── engine.out.log          # Engine stdout
└── engine.err.log          # Engine stderr
```

## What's Been Implemented

### Agent Creation & Full Isolation
- Each agent gets own HOME directory with complete Conway stack
- Bootstrap script pre-installs: Conway Terminal, provisions API key, configures OpenClaw
- Wallet and config synced to .anima/ so engine reuses same identity
- .automaton → .anima symlink for backward compatibility
- auto-config.json with proper creator ETH address
- Per-agent Telegram credentials (required for creation)
- Full agent deletion with wallet safety check

### Genesis Prompt (Completely Rewritten)
- Reduced from 490 lines (~25KB) to ~100 lines (~5.8KB)
- Agent starts with tools ALREADY INSTALLED (50+ Conway tools from Turn 1)
- Clear 3-step startup: Telegram → Verify Tools → Condense SOUL.md
- Revenue strategies, financial discipline, security rules — all compact
- Template variables: {{AGENT_NAME}}, {{TELEGRAM_BOT_TOKEN}}, {{TELEGRAM_CHAT_ID}}

### Infrastructure Monitoring
- Overview: Stats grid (Sandboxes, Domains, Tools, Agents, Messages, URLs)
- Sandboxes: VM list with status, resources, public URLs, expandable details
- Terminal: Read-only dark-themed terminal (exec/sandbox_exec outputs)
- Domains: Registered domains with DNS records
- Installed Tools: MCP servers, npm packages, ClawHub skills
- Agent Network: Discovered agents + agent-to-agent messages

### Comprehensive Activity Feed
- ALL agent actions: tool calls, transactions, on-chain TXs, messages, modifications, heartbeats
- Category filters: infrastructure, compute, finance, network, domains, orchestrator, tools, inference, memory, system
- Real-time polling every 8 seconds

### UI Stability (Critical Bug Fixed)
- viewRef pattern: checkStatus useCallback has [] dependency, reads view via ref
- Content-based comparison: logs, turns, agents compared by content not just count
- Balance persists across polling cycles
- Agent switch properly resets all state

### Deployment Readiness
- All credentials from .env files (no hardcoded values)
- No exposed secrets in code (test files with tokens cleaned)
- Frontend: process.env.REACT_APP_BACKEND_URL everywhere
- Backend: os.environ.get() for all credentials
- Deployment agent confirmed: PASS on all checks

## Key API Endpoints (All Return 200)
- `POST /api/agents/create` — Create agent with full bootstrap
- `POST /api/agents/{id}/start` — Start engine with pre-bootstrap
- `POST /api/agents/{id}/select` — Switch active agent context
- `GET /api/genesis/status` — Agent status, wallet, engine state
- `GET /api/engine/logs` — Agent-specific logs
- `GET /api/wallet/balance` — Live on-chain USDC balance
- `GET /api/live/identity` — Agent identity from state.db
- `GET /api/live/turns` — Live turn data from engine
- `GET /api/live/soul` — SOUL.md content
- `GET /api/infrastructure/overview` — Infrastructure summary
- `GET /api/infrastructure/sandboxes` — VM/Sandbox list
- `GET /api/infrastructure/terminal` — Read-only terminal output
- `GET /api/infrastructure/domains` — Registered domains
- `GET /api/infrastructure/installed-tools` — Installed MCP tools
- `GET /api/infrastructure/activity-feed` — Comprehensive activity feed
- `GET /api/skills/available` — All 141 skills
- `GET /api/agents` — Agent list
- `GET /api/telegram/status` — Telegram config status

## Testing Status
- Iteration 37: 32/32 tests passed (UI stability + polling fixes)
- Iteration 38: 28/28 tests passed (Infrastructure + Activity pages)
- Iteration 39: 52/52 tests passed (Deployment readiness, security, isolation)
- Deployment agent: PASS (no blockers)

## P0 (All Completed)
- [x] UI flashing/instability fix (viewRef pattern)
- [x] Genesis prompt rewrite (lean, effective)
- [x] Agent bootstrap with Conway Terminal pre-install
- [x] Directory alignment (.anima as primary, .automaton symlink)
- [x] Infrastructure monitoring page (6 tabs)
- [x] Comprehensive activity feed with category filters
- [x] Agent isolation (full data separation)
- [x] Deployment readiness (no secrets, env-only config)

## P1 (Next — Post-Deployment)
- [ ] Test live agent behavior with new lean genesis prompt
- [ ] Verify sandbox data flows to Infrastructure page with real agent activity
- [ ] Backend Telegram auto-relay for infrastructure events

## P2 (Backlog)
- [ ] Real smart contracts implementation
- [ ] Android device control integration
- [ ] Self-hosted infrastructure migration
- [ ] React Query/SWR migration for polling
