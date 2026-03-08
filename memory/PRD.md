# Anima Fund - PRD

## Problem Statement
Fully autonomous AI-to-AI VC fund platform. Multi-agent system where each agent is sovereign — installs its own tools, discovers skills, operates freely on the live internet with no restrictions.

## Architecture
- **Frontend**: React (port 3000) — dashboard for agent monitoring
- **Backend**: FastAPI (port 8001) — reads engine state.db, manages agent metadata in MongoDB
- **Database**: MongoDB (anima_fund) — agent metadata only
- **Engine**: Conway Automaton (`/app/scripts/start_engine.sh` → `/app/automaton/dist/bundle.mjs`)
- **Agent Home**: Per-agent at `~/agents/{id}/` with `HOME` env var set

## Genesis Prompt v6 (Feb 2026 — from full docs.conway.tech scrape)
Comprehensive 21K char template covering ALL Conway capabilities:
- **Hard-gated Phase 0**: Blocks goals/code/building until OpenClaw + Conway verified
- **curl fallback**: python3 urllib for all downloads (curl often missing)
- **Sandbox workflow**: sandbox_create → sandbox_expose_port = public URLs (NOT expose_port = localhost)
- **Custom subdomains**: https://{name}.life.conway.tech
- **Full deploy flow**: sandbox → expose port → register domain → CNAME
- **All inference models**: GPT-5.2, Claude Opus 4.6, Gemini 3 Pro/Flash, Kimi K2.5, Qwen3
- **Domain management**: search, register, DNS CRUD, WHOIS privacy, nameservers
- **PTY sessions**: Interactive terminals for REPLs, vim, shells
- **Sandbox specs**: 1-4 vCPU, 512-8192 MB RAM, 1-50 GB disk, 2 regions
- **Revenue freedom**: Trade, services, data, infrastructure, social — building is last resort
- **Complete isolation**: Zero traceability, identity firewall, clean deployments
- **Financial discipline**: Balance checks, ROI evaluation, search-before-build
- **SOUL.md condensation**: After Phase 0, condense to <2000 chars (save context)
- **Goal orchestrator rules**: No create_goal before Phase 0, single active goal, work with orchestrator
- **Problem-solving protocol**: Never say "I can't" — search ClawHub/MCPs/npm/PyPI/GitHub for tools
- **Continuous self-upgrade**: Every 10 turns search for new capabilities
- **Broad tool discovery**: ClawHub, MCP registries (mcp.so, smithery.ai, GitHub), npm, PyPI, x402

## Multi-Agent Isolation
- Per-agent data directory, log files, creator wallets (from MongoDB)
- Active agent ID tracked with file persistence
- Engine start passes per-agent HOME + Telegram env vars

## Key Fixes Applied
- Engine start path: `/app/scripts/start_engine.sh` (was broken — wrong relative path)
- Per-agent Telegram env vars on engine start
- `include_conway` regex updated for new prompt format
- `expose_port` vs `sandbox_expose_port` clearly documented in prompt

## Testing Status
- Iteration 36: 25/25 backend, 11/11 frontend — 100% pass
- All endpoints verified: health, genesis/status, engine/live, engine/logs, agents, skills, wallet

## Future Tasks
- P1: Real Smart Contracts (Solidity)
- P2: Android Device Control
- P2: Self-Hosted Infrastructure
