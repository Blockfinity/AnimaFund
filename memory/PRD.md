# Anima Fund — Product Requirements Document

## Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform named "Anima Fund". Deploy and monitor multiple AI agents from a single dashboard, each with their own wallet, Telegram bot, goals, and revenue share to creator.

## Architecture
- **Frontend**: React (CRA) at port 3000
- **Backend**: FastAPI at port 8001 (modular router architecture)
- **Database**: MongoDB (agents collection), SQLite (state.db per agent)
- **Agent Engine**: Conway Research Automaton (OpenClaw runtime)
- **Infrastructure**: Conway Cloud (sandboxes, compute, domains, x402 payments)
- **Multi-Agent**: Each agent gets isolated HOME dir at `~/agents/{id}/` with `$HOME/.automaton/`

## Backend Architecture
```
backend/
├── server.py              # Slim main: lifespan, CORS, health, router includes
├── database.py            # Shared MongoDB init/close/get_db
├── config.py              # Shared constants
├── engine_bridge.py       # Live engine data bridge (reads from active agent's state.db)
├── payment_tracker.py     # Financial enforcement
├── telegram_notify.py     # Telegram notification helper
└── routers/
    ├── agents.py          # Agent CRUD, 141-skill listing (9 sources)
    ├── genesis.py         # Genesis creation, wallet, engine management
    ├── live.py            # All /api/live/* endpoints (25+)
    └── telegram.py        # Telegram send/status
```

## Skills Architecture (141 skills, 9 sources)
- **Anima Fund (96)**: Custom skills in `/app/automaton/skills/`
- **Conway Cloud (6)**: sandbox_create, sandbox_exec, sandbox_expose_port, etc.
- **Conway Compute (1)**: chat_completions (GPT-4o, o3-mini, Claude, Kimi)
- **Conway Domains (3)**: domain_search, domain_register, domain_dns_add
- **Conway x402 (3)**: wallet_info, x402_fetch, x402_discover
- **Conway Credits (2)**: credits_balance, credits_pricing
- **OpenClaw (12)**: browse_page, browser, discover_agents, send_message, spawn_child, create_skill, etc.
- **ClawHub Marketplace (15)**: web-browsing, telegram-integration, github, docker-essentials, etc. (install via `clawhub install`)
- **Engine (3)**: Skills discovered from live state.db

## What's Been Implemented
- [x] Full 10-page dashboard (Agent Mind, Fund HQ, Agents, Skills, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration)
- [x] Real-time engine bridge from per-agent state.db
- [x] 96 custom Anima skills + Conway/OpenClaw/ClawHub marketplace
- [x] Multi-Agent Dashboard with full isolation (wallet, logs, soul, turns all per-agent)
- [x] Agent selection persists across server restarts
- [x] Genesis Prompt v4: Conway Terminal tools, ClawHub marketplace, native Telegram (no curl), anti-loop/anti-block
- [x] Backend refactored into modular FastAPI routers
- [x] OPSEC: Constitution Article XIII, genesis prompt security section
- [x] Constitution push endpoint for live agents
- [x] Wallet mismatch detection
- [x] Skills page: 141 skills from 9 sources with source badges and install status
- [x] Skill selector: individual click toggle, source badges, search
- [x] Log feed: no snap-to-top, stable tab switching, adaptive polling
- [x] No localhost references anywhere
- [x] E2E tested: iterations 19-26 all 100% pass

## Upcoming Tasks
- P2: Review and enhance 96 custom Anima skills for real-world functionality

## Future Tasks
- Real smart contracts for trustless fee/revenue splits
- Android device control integration
- Self-hosted infrastructure migration
