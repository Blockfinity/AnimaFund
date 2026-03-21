# Anima Platform — Product Requirements

## FORK_PROMPT.md is the definitive source of truth.

## What EXISTS and WORKS (March 21, 2026)

### Ultimus (THE CORE PRODUCT) — NOW EXISTS
- /app/ultimus/predictor.py — Multi-persona simulation with LLM-powered agents
- /app/ultimus/calculator.py — Cost/feasibility/deployment wave planning
- /app/ultimus/executor.py — Converts personas to real Anima deployments
- /app/ultimus/api.py — REST endpoints (POST /api/ultimus/predict, GET /predictions, POST /execute)
- Frontend: Ultimus page with goal input, mode selector, simulation, results view, cost model, execute button
- TESTED: "Make $1000 in memecoins" → 3 personas, 2 rounds, strategy with 0.7 confidence, self-sustaining cost model
- Still missing: dimensions.py, knowledge.py, personas.py (GraphRAG + Dimensions screens)

### Backend (10 routers, 1,584 lines)
- server.py, provision.py, monitor.py, webhook.py, spawn.py, agents.py, telegram.py + 3 legacy

### Anima Machina (CAMEL fork)
- 95 toolkits, 3 custom (Wallet, Spawn, StateReporting)
- Rebrand: comments/logs changed, imports stay as `from camel.` (package name)

### Dashboard (15 pages now)
- Ultimus (NEW), AgentMind, AnimaVM, FundHQ, Agents, Infrastructure, Skills, DealFlow, Portfolio, Financials, Activity, Memory, Configuration, Wallet

### Conway sandbox: 9 cents (dead). Catalyst wallet: $3 USDC.

## Still Missing
- Dimensions (God's-eye view) — frontend + backend
- GraphRAG knowledge.py for seed data
- Multi-agent dashboard (agent selector, overview, aggregates)
- Spawn via webhook (records only, doesn't provision)
- x402 real payments
- Generic BYOI (Conway only)
- JWT auth
- Ultima X integration
- Full rebrand of CAMEL internals
