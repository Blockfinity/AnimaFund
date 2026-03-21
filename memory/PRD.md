# Anima Platform — Product Requirements

## FORK_PROMPT.md is the definitive source of truth.

## What EXISTS (March 21, 2026)

### Ultimus (CORE) — predictor + calculator + executor + api + frontend
- POST /api/ultimus/predict — multi-persona simulation, tested with real prediction
- POST /api/ultimus/execute — deploys agents from prediction strategy
- Frontend: MiroFish-inspired 5-phase flow, no boxes, compact data-dense layout

### Dimensions (God's-Eye View) — simulation viewer + live viewer + chat + injection
- GET /api/dimensions/simulation/{id} — load simulated world with personas + relationships
- GET /api/dimensions/live — all running Animas with state
- POST /api/dimensions/chat — LLM-powered chat with any persona or live Anima
- POST /api/dimensions/inject — inject variables into simulations
- Frontend: 3-column layout with force-directed graph canvas, compact entity list, chat panel

### Spawn via Webhook — IMPLEMENTED
- Agents send {"type": "spawn_request"} through WEBHOOK_URL
- Records in MongoDB, no new URL exposed

### Multi-Agent Foundation — IMPLEMENTED
- /api/live/agents returns ALL agents with state, financials, prediction_id
- App.js has selectedAgent state and agent selector dropdown
- Dashboard pages accept selectedAgent prop

### Dashboard: 16 pages
- Ultimus, Dimensions + 14 existing pages

### Backend: 15+ active endpoints across ultimus, dimensions, monitor, webhook, spawn, agents

## Still Missing
- Knowledge graph (GraphRAG) for Deep/Expert modes
- x402 real payments
- Generic BYOI (Conway only)
- JWT auth
- Ultima X integration
- Full CAMEL internals rebrand
- Conway credits ($0.09 — sandbox dead)
