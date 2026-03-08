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
│   ├── server.py           # FastAPI main app
│   ├── engine_bridge.py    # Reads agent data from SQLite state.db
│   ├── config.py           # Shared constants
│   ├── database.py         # MongoDB connection
│   └── routers/
│       ├── agents.py       # Agent CRUD, bootstrap, engine start
│       ├── genesis.py      # Status, logs, wallet balance, prompt template
│       ├── live.py         # Live agent data (turns, soul, identity)
│       ├── infrastructure.py # VM/Sandbox monitoring, terminal, domains, activity feed
│       └── telegram.py     # Telegram notification relay
├── frontend/src/
│   ├── App.js              # Router, polling (stable useCallback with viewRef)
│   ├── pages/
│   │   ├── AgentMind.js    # Real-time agent monitoring (stable polling)
│   │   ├── Infrastructure.js # VM/Sandbox/Domains/Terminal/Tools/Network monitoring
│   │   ├── Activity.js     # Comprehensive activity feed with category filters
│   │   ├── FundHQ.js       # Fund overview
│   │   ├── Agents.js       # Agent list
│   │   └── Skills.js       # Skills browser (141 skills)
│   └── components/
│       ├── Sidebar.js      # Navigation (includes Infrastructure)
│       └── CreateAgentModal.js  # Agent creation with Telegram verification
└── scripts/
    ├── start_engine.sh     # Engine starter (runs bootstrap first)
    └── bootstrap_agent.sh  # Pre-installs Conway Terminal + OpenClaw
```

## What's Been Implemented

### Agent Creation & Isolation
- Full agent isolation: each agent gets own HOME directory, data dir, logs
- auto-config.json with proper creator address (fixed from hardcoded zero)
- Pre-bootstrap script installs Conway Terminal + configures OpenClaw before engine starts
- Per-agent Telegram credentials (required for creation)

### Genesis Prompt (Completely Rewritten)
- Reduced from 490 lines (~25KB) to ~100 lines (~5.8KB)
- Agent starts with tools ALREADY INSTALLED (no Phase 0 bootstrap needed)
- Clear 3-step startup: Telegram → Verify Tools → Condense SOUL.md
- Complete tools reference kept but concise
- Revenue strategies, financial discipline, security rules all compact

### Infrastructure Monitoring (NEW)
- **Overview tab**: Stats grid showing Sandboxes, Domains, Installed Tools, Discovered Agents, Messages, Public URLs
- **Sandboxes tab**: Lists all Conway Cloud VMs with status, resources, public URLs
- **Terminal tab**: Read-only dark-themed terminal showing all exec/sandbox_exec output
- **Domains tab**: Registered domains with DNS records
- **Installed Tools tab**: MCP servers, npm packages, ClawHub skills
- **Agent Network tab**: Discovered agents and agent-to-agent messages

### Comprehensive Activity Feed (ENHANCED)
- ALL agent actions in one stream: tool calls, transactions, on-chain TXs, messages, modifications, heartbeats
- Category-based filtering: infrastructure, compute, finance, network, domains, orchestrator, tools, inference, memory, system
- Real-time polling every 8 seconds

### UI Stability (Critical Bug Fixed)
- Fixed useCallback dependency: `checkStatus` now uses `[]` with `viewRef`
- Fixed log comparison: content-based instead of count-only
- Balance fetch resets on agent switch
- Polling interval stable, never re-created

### Live Feed Enhancement
- Enhanced log parser: recognizes Conway engine format timestamps
- 14 log tags: TOOL, ORCH, SANDBOX, NETWORK, FINANCE, TURN, etc.

### Skills & Models
- Updated model names: GPT-5.2, Claude Opus 4.6, Gemini 3, Kimi K2.5, Qwen3
- 141 skills available

## Key API Endpoints
- `POST /api/agents/create` — Create agent with bootstrap
- `POST /api/agents/{id}/start` — Start engine with pre-bootstrap
- `GET /api/genesis/status` — Agent status, wallet, engine state
- `GET /api/engine/logs` — Agent-specific logs
- `GET /api/wallet/balance` — Live on-chain balance
- `GET /api/infrastructure/overview` — Infrastructure summary
- `GET /api/infrastructure/sandboxes` — VM/Sandbox list
- `GET /api/infrastructure/terminal` — Read-only terminal output
- `GET /api/infrastructure/domains` — Registered domains
- `GET /api/infrastructure/installed-tools` — Installed MCP tools
- `GET /api/infrastructure/activity-feed` — Comprehensive activity feed

## 3rd Party Integrations
- Conway Research: Terminal, Cloud, Compute, Domains (via MCP)
- OpenClaw: Browser automation, agent network, skills
- ClawHub: Skill marketplace
- Telegram Bot API: Real-time agent reporting

## P0 (Completed)
- [x] UI flashing/instability fix
- [x] Genesis prompt rewrite (lean, effective)
- [x] Auto-config creator address fix
- [x] Agent bootstrap script (Conway Terminal pre-install)
- [x] Infrastructure monitoring page (6 tabs)
- [x] Comprehensive activity feed with category filters
- [x] Live Feed enhancement (better log parsing, new tags)
- [x] Model names update

## P1 (Next)
- [ ] Verify agent bootstrap works end-to-end with live Conway Terminal install
- [ ] Test agent creation flow with real Telegram credentials
- [ ] Monitor agent behavior with new lean genesis prompt
- [ ] Add real-time Telegram relay for infrastructure events

## P2 (Backlog)
- [ ] Implement real smart contracts
- [ ] Android device control integration
- [ ] Self-hosted infrastructure migration
- [ ] React Query/SWR migration for polling
