# Anima Platform — Product Requirements

## FORK_PROMPT.md is the definitive source of truth.

## What EXISTS and WORKS (March 21, 2026)

### Ultimus (CORE PRODUCT) — BUILT
- predictor.py — Multi-persona LLM simulation (tested: 3 personas, 2 rounds, 0.7 confidence)
- calculator.py — Cost model, deployment waves, break-even, self-sustaining analysis
- executor.py — Converts strategy to real Anima deployments with auto-generated genesis prompts
- api.py — POST /api/ultimus/predict, GET /predictions, POST /execute
- Frontend: MiroFish-inspired 5-phase UI (Seed Input → Simulation → Strategy → Cost Review → Execute)
  - Persona cards, system dashboard, cost model panel, deployment agent list, execute button
  - Past predictions list with status

### Dimensions (GOD'S-EYE VIEW) — BUILT
- dimensions.py — Simulation world viewer, live agent viewer, chat with any persona, variable injection
- API: GET /api/dimensions/status, GET /simulation/{id}, GET /live, POST /chat, POST /inject
- Frontend: 3-panel layout (worlds/personas list | entity detail | chat panel)
  - Simulation mode: load completed predictions, observe personas, chat with them
  - Live mode: observe real running Animas, chat with them
  - Variable injection for re-running scenarios

### Spawn via Webhook — IMPLEMENTED
- Agents send {"type": "spawn_request"} through existing WEBHOOK_URL
- No new URL exposed to sandbox
- Records in MongoDB with parent_agent_id, genesis_prompt, specs

### Dashboard (16 pages now)
- Ultimus, Dimensions, AgentMind, AnimaVM, FundHQ, Agents, Infrastructure, Skills,
  DealFlow, Portfolio, Financials, Activity, Memory, Configuration, Wallet, AgentSetup

### Backend (13 endpoints active)
- ultimus/predict, ultimus/predictions, ultimus/execute, ultimus/status
- dimensions/status, dimensions/simulation/{id}, dimensions/live, dimensions/chat, dimensions/inject
- agents, provision, monitor, webhook, spawn, telegram + legacy

## Still Missing
- Knowledge graph (GraphRAG) for Deep/Expert predict modes
- Multi-agent dashboard (agent selector, overview, aggregates)
- x402 real payments
- Generic BYOI (Conway only, no second provider)
- JWT auth
- Ultima X integration
- Full CAMEL internals rebrand
- Conway credits (9 cents — sandbox dead)
