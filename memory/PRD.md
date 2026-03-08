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
│       └── live.py         # Live agent data (turns, soul, identity)
├── frontend/src/
│   ├── App.js              # Router, polling (stable useCallback with viewRef)
│   ├── pages/
│   │   ├── AgentMind.js    # Real-time agent monitoring (stable polling)
│   │   ├── FundHQ.js       # Fund overview
│   │   ├── Agents.js       # Agent list
│   │   └── Skills.js       # Skills browser (141 skills)
│   └── components/
│       └── CreateAgentModal.js  # Agent creation with Telegram verification
└── scripts/
    ├── start_engine.sh     # Engine starter (runs bootstrap first)
    └── bootstrap_agent.sh  # Pre-installs Conway Terminal + OpenClaw
```

## What's Been Implemented

### Agent Creation & Isolation
- Full agent isolation: each agent gets own HOME directory, data dir, logs
- auto-config.json with proper creator address (was hardcoded to zero)
- Pre-bootstrap script installs Conway Terminal + configures OpenClaw before engine starts
- Per-agent Telegram credentials (required for creation)

### Genesis Prompt (Completely Rewritten)
- Reduced from 490 lines (~25KB) to ~100 lines (~5.8KB)
- Agent starts with tools ALREADY INSTALLED (no Phase 0 bootstrap needed in prompt)
- Lean SOUL.md: agent condensed from massive document to focused identity
- Clear 3-step startup: Telegram → Verify Tools → Condense SOUL.md
- Complete tools reference kept but concise
- Revenue strategies, financial discipline, security rules all present but compact

### UI Stability (Critical Bug Fixed)
- Fixed useCallback dependency: `checkStatus` now uses `[]` with `viewRef` (was `[view]`)
- Fixed log comparison: content-based (prevLast === newLast) instead of count-only
- Fixed turns/agents comparison to detect actual data changes
- Balance fetch resets on agent switch via `selectedAgent` dependency
- Polling interval stable at 8 seconds, never re-created

### Live Feed Enhancement
- Enhanced log parser: recognizes Conway engine format timestamps
- New log tags: TOOL, ORCH, SANDBOX, NETWORK, FINANCE, TURN (was only 8 tags, now 14)
- Tag colors updated for all new categories
- Important entries highlighted with left border

### Skills & Models
- Updated model names: GPT-5.2, Claude Opus 4.6, Gemini 3, Kimi K2.5, Qwen3
- 141 skills available across Anima, Conway, OpenClaw, ClawHub sources

## Key API Endpoints
- `POST /api/agents/create` — Create agent with bootstrap
- `POST /api/agents/{id}/start` — Start engine with pre-bootstrap
- `POST /api/agents/{id}/select` — Switch active agent
- `GET /api/genesis/status` — Agent status, wallet, engine state
- `GET /api/engine/logs` — Agent-specific logs
- `GET /api/wallet/balance` — Live on-chain balance
- `GET /api/live/turns` — Live turn data from engine
- `GET /api/live/soul` — SOUL.md content
- `GET /api/skills/available` — All 141 skills
- `GET /api/genesis/prompt-template` — Lean genesis prompt

## DB Schema (MongoDB)
- **agents** collection: agent_id, name, agent_home, data_dir, telegram_bot_token, telegram_chat_id, creator_sol_wallet, creator_eth_wallet, status, engine_pid

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
- [x] Live Feed enhancement (better log parsing, new tags)
- [x] Model names update

## P1 (Next)
- [ ] Verify agent bootstrap works end-to-end with live Conway Terminal install
- [ ] Test agent creation flow with real Telegram credentials
- [ ] Monitor agent behavior with new lean genesis prompt

## P2 (Backlog)
- [ ] Implement real smart contracts (replace instruction-based financial logic)
- [ ] Android device control integration
- [ ] Self-hosted infrastructure migration
- [ ] React Query/SWR migration for polling (would eliminate all polling bugs permanently)
