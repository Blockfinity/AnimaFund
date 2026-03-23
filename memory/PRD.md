# Anima Platform — PRD (Updated March 23, 2026)

## Original Problem Statement
Build a platform to launch and monitor fully autonomous agents ("Animas") in isolated, sandboxed environments. Core components:
- **Ultimus Simulation Engine**: Multi-agent simulation using Anima Machina (CAMEL-AI fork)
- **Anima Runtime**: Agent framework with browser, shell, memory, wallet toolkits
- **BYOI (Bring Your Own Infrastructure)**: Conway Cloud + Fly.io providers
- **Self-Propagating Economy**: Agents seeded with funds, must generate revenue

## Architecture
```
/app/backend/        — FastAPI platform API (server.py + 10 routers)
/app/frontend/       — React dashboard (16 pages including Ultimus)
/app/ultimus/        — Prediction engine (predictor, calculator, executor, dimensions, knowledge, api)
/app/anima-machina/  — Agent framework (CAMEL fork, fully rebranded)
/app/engine/         — Agent runners + skills + templates
/app/ultima-x/       — Inference model config
/app/docs/           — Architecture documentation
```

## What's Implemented
- [x] Ultimus Simulation Engine (multi-round, multi-agent with Workforce)
- [x] Anima Machina Runtime (7/7 toolkits working)
- [x] UI Redesign (react-force-graph-2d, MiroFish-inspired)
- [x] Knowledge Graph extraction (Deep/Expert modes)
- [x] Agent Execution (subprocess isolation)
- [x] Wallet Architecture (two-wallet core/public system)
- [x] BYOI Conway + Fly.io providers
- [x] Per-agent provider key management (fly_api_key stored in MongoDB per agent)
- [x] Provider key endpoints: provider-key-status, set-provider-key
- [x] Sandbox management: health-check, reset-sandbox, delete-sandbox
- [x] Deployment preparation (clean requirements.txt, optimized startup)

## Bug Fixes (March 23, 2026)
- **FIXED**: "Adding Fly API key for new agent fails" — Root cause: 5 missing backend endpoints (provider-key-status, set-provider-key, health-check, reset-sandbox, delete-sandbox). Also fixed _get_provider to read per-agent Fly keys from MongoDB instead of only env vars.

## Prioritized Backlog

### P0 (Critical)
- [ ] Wallet Transaction Test — Execute real send_payment on-chain
- [ ] Docker Containerization — Replace subprocess with Docker containers

### P1 (High)
- [ ] Multi-Agent Dashboard Live Data — Graph view with all deployed agents
- [ ] Connect Frontend to SSE Stream — Live simulation updates
- [ ] Multi-Agent Selector Dropdown — Backend supports it, UI needs it

### P2 (Medium)
- [ ] Spawn via Webhook — Provision new environments from spawn_request
- [ ] Ultimus Calculator — Wire cost estimates into frontend
- [ ] Ultimus Execute Flow — Full end-to-end large-scale simulation

### P3 (Low/Future)
- [ ] Generic BYOI Interface — Abstract provider interface with mock provider
- [ ] JWT Authentication — Secure all platform endpoints
- [ ] Ultima X Integration — Self-hosted model as inference option
- [ ] Anima Machina Rebrand Cleanup — Internal "camel" references in forked package

## Environment Variables
MONGO_URL, DB_NAME, REACT_APP_BACKEND_URL, EMERGENT_LLM_KEY, OPENAI_API_KEY,
OPENAI_API_BASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, CONWAY_API_KEY,
FLY_API_TOKEN, FLY_APP_NAME, CREATOR_WALLET, CREATOR_ETH_ADDRESS

## Key DB Schema
- **agents**: `{ agent_id, name, genesis_prompt, fly_api_key, fly_app_name, conway_api_key, llm_api_key, llm_base_url, llm_model, status, provisioning: {...} }`
- **predictions**: `{ prediction_id, goal, status, personas, rounds, events, relationships, strategy }`
