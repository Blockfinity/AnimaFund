# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform where independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via the Conway ecosystem.

## Architecture
- **Frontend**: React (port 3000) with shadcn/ui
- **Backend**: FastAPI (port 8001) with MongoDB
- **Agent Engine**: Automaton TypeScript runtime (`dist/bundle.mjs`) with SQLite state.db
- **Conway Integration**: Native Conway API client + Conway Terminal MCP server
- **External Services**: Conway Cloud, Conway Compute, Conway Domains, Telegram Bot API

## Conway Ecosystem Integration (COMPLETE)

### Conway Cloud (api.conway.tech)
- Sandboxes: Create, list, delete Linux VMs
- Execution: Run commands and code in sandboxes
- Files: Upload, download, list files
- Ports: Expose ports, custom subdomains on life.conway.tech
- PTY Sessions: Interactive terminal sessions
- Web Terminal: Browser-based sandbox access

### Conway Compute (inference.conway.tech)
- Chat Completions API (OpenAI-compatible)
- Models: gpt-5.2, claude-opus-4.6, claude-sonnet-4.5, gemini-2.5-pro, kimi-k2.5, qwen3-coder
- Streaming SSE support
- Billed from Conway credits

### Conway Domains (api.conway.domains)
- Domain search, registration, renewal
- DNS management (CRUD)
- SIWE/SIWS wallet authentication
- x402 USDC payments

### Conway Terminal (MCP Server)
- Installed globally: conway-terminal v2.0.9
- Config at: ~/.conway/config.json + ~/.conway/wallet.json
- OpenClaw MCP config at: ~/.openclaw/config.json
- 36 MCP tools available to agents

### Automatons (Identity Registration)
- EIP-712 signed identity registration
- Immutable: automaton_address, creator_address, name, bio, genesis_prompt_hash

## Backend API Endpoints

### Conway API Router (`/api/conway/*`) — NEW
- `GET /api/conway/balance` — Real-time credits + sandbox count
- `GET /api/conway/health` — All 3 Conway services health
- `GET /api/conway/sandboxes` — List sandboxes from Conway Cloud
- `GET /api/conway/credits/pricing` — VM and credit tiers
- `GET /api/conway/credits/history` — Credit transaction history
- `GET /api/conway/domains/search` — Public domain search
- `GET /api/conway/inference/health` — Inference API status

### Existing Routers
- `agents.py` — Multi-agent CRUD, 141 skills across 9 sources
- `genesis.py` — Agent creation/reset, status, prompt template
- `live.py` — 25+ endpoints reading from state.db
- `infrastructure.py` — Sandbox/domain/terminal data from tool_calls
- `telegram.py` — Telegram bot health/config

## Frontend Pages (11)
Agent Mind, Fund HQ, Agents, Infrastructure, Skills, Deal Flow, Portfolio, Financials, Activity, Memory, Configuration, Wallet & Logs

## What's Been Implemented
- [x] Full multi-agent dashboard with real-time data from state.db
- [x] Conway API integration (all 3 services: Cloud, Compute, Domains)
- [x] Conway Terminal installed and provisioned (v2.0.9)
- [x] OpenClaw MCP configuration
- [x] Bootstrap script for agent environment setup
- [x] Genesis prompt with anti-loop rules and Conway tool guidance
- [x] Wallet balance with on-chain USDC/ETH + Conway credits
- [x] Skills catalog with 141 skills (Conway, OpenClaw, ClawHub, Engine, Anima)
- [x] Infrastructure dashboard (sandboxes, domains, terminal, tools, network)
- [x] Telegram bot integration for agent communication
- [x] Agent identity registration (EIP-712)
- [x] Deployment verified and ready

## Current State
- Conway API key: Active (cnwy_k_...)
- Credits: $0.00 (CRITICAL tier)
- Live agent: Dead (0 credits, stuck in loop)
- Engine: SLEEPING (not running)

## Next Steps (P0)
- Fund Conway wallet with credits
- Create NEW agent with improved genesis prompt
- Verify agent operates correctly via dashboard

## Future/Backlog
- Real smart contracts integration
- Android device control
- Self-hosted agent engine migration
- Revenue tracking charts
- Multi-agent communication dashboard
