# Anima Fund - PRD

## Problem Statement
Fully autonomous AI-to-AI VC fund platform. Multi-agent system where each agent is sovereign — installs its own tools, discovers skills, operates freely on the live internet.

## Architecture
- **Frontend**: React (port 3000) — dashboard for agent monitoring
- **Backend**: FastAPI (port 8001) — reads engine state.db, manages agent metadata in MongoDB
- **Database**: MongoDB (anima_fund) — agent metadata only
- **Engine**: External autonomous agent runtime
- **Agent Setup**: Each agent bootstraps itself via genesis prompt

## Genesis Prompt Design (v5 — Feb 2026, sourced from full docs.conway.tech scrape)
Comprehensive template covering every Conway capability:
- **Hard-gated Phase 0** — Nothing happens until OpenClaw + Conway verified
- **Correct sandbox workflow**: sandbox_create → sandbox_expose_port (public URL), NOT expose_port (localhost)
- **Public URLs**: https://{port}-{id}.life.conway.tech or custom https://{name}.life.conway.tech
- **Full deploy flow**: sandbox → expose port → register domain → CNAME → real service
- **All inference models**: GPT-5.2/5-mini/5-nano, Claude Opus 4.6/Sonnet 4.5/Haiku 4.5, Gemini 3 Pro/Flash, Kimi K2.5, Qwen3
- **Domain management**: search, register, DNS CRUD, WHOIS privacy, nameservers — all via x402 USDC
- **PTY sessions**: Interactive terminals for REPLs, vim, shells
- **Sandbox specs**: 1-4 vCPU, 512-8192 MB RAM, 1-50 GB disk, regions eu-north/us-east
- **Broad tool discovery**: ClawHub, MCP registries (mcp.so, smithery.ai, GitHub), npm, PyPI, GitHub, x402 services, other agents
- **Revenue freedom**: Trade, services, data, infrastructure, social — building is last resort
- **Complete isolation**: Zero traceability, identity firewall, clean deployments
- **Financial discipline**: Balance checks, ROI evaluation, search-before-build
- **Continuous self-upgrade**: Every 10 turns search for new tools

## Features Implemented
- Multi-agent platform with isolated data directories
- Per-agent log, wallet, and creator wallet isolation
- Real-time dashboard (Agent Mind, Fund HQ, Skills)
- Per-agent Telegram bot with background log forwarding
- UI stability (sticky display, no flash on polling)
- Sovereign genesis prompt with full Conway docs coverage

## Key Endpoints
- `POST /api/agents/create` — genesis-prompt.md + auto-config.json
- `POST /api/agents/{id}/select` — switch active agent
- `GET /api/genesis/status` — per-agent data
- `GET /api/genesis/prompt-template` — genesis prompt template
- `GET /api/engine/live` — engine state
- `GET /api/engine/logs` — per-agent logs
- `GET /api/wallet/balance` — per-agent balance

## Testing
- Iteration 35: 17/17 backend, 7/7 frontend — 100% pass

## Future Tasks
- P1: Real Smart Contracts (Solidity)
- P2: Android Device Control
- P2: Self-Hosted Infrastructure
