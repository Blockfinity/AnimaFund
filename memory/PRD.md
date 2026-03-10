# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform. Agent runs inside Conway Cloud sandbox, creates its own wallet, must earn $5k before building products (by any means necessary), then $10k before creating the fund.

## Architecture — ZERO HOST EXECUTION (Mar 2026 refactor)
- **Host**: Dashboard API + static file serving ONLY. No agent engine, no wallet, no subprocess.
- **Conway Sandbox**: Agent lives and runs here exclusively (engine, wallet, tools, files, state.db)
- **Frontend**: React (port 3000)
- **Backend**: FastAPI (port 8001) — reads provisioning status, routes to Conway API
- **Database**: MongoDB (anima_fund) — agent configs, creation metadata
- **Agent Engine**: Conway Automaton (runs INSIDE sandbox only)

### Data flow:
- Dashboard → Provisioning Status JSON (local file, updated by Conway API responses)
- Dashboard → Conway Cloud API (sandbox exec, files, terminal)
- Dashboard → On-chain RPC (wallet balance checks)
- Dashboard → MongoDB (agent configs)
- NO host filesystem reads for agent state
- NO host subprocess spawning
- NO engine_bridge host SQLite reads

## Conway Payment Model
- **Sandbox compute**: Paid by Conway API key credits (CONWAY_API_KEY in .env)
- **Agent wallet**: Created INSIDE sandbox by Conway Terminal (step 2 of provisioning)
- **Agent wallet used for**: x402 payments (domains, paid APIs, services)
- **No chicken-and-egg**: API key pays for VM creation, wallet comes later

## Onboarding Flow
1. Open app → Genesis screen with 6-step provisioning stepper
2. Create Sandbox → Install Terminal (wallet created here) → Install OpenClaw → Claude Code → Load Skills → Create Anima
3. After wallet created → QR code displayed for funding
4. After Create Anima → "Open Dashboard" button
5. Dashboard → AnimaVM monitoring page (status bar + 7 tabs)

## Disabled Endpoints (security: nothing on host)
- `POST /api/genesis/create` → returns error "Use provisioning stepper"
- `POST /api/agents/{id}/start` → returns error "Engines run in sandbox"
- All `live/*` endpoints → return empty defaults (no host engine)
- All `infrastructure/*` endpoints → return empty defaults

## Active Endpoints
- `GET /api/genesis/status` → reads from provisioning-status.json
- `GET /api/wallet/balance` → on-chain RPC check for sandbox wallet
- `GET /api/engine/live` → sandbox exec to check if engine process running
- `GET /api/engine/logs` → sandbox exec to read log files
- All provision/* endpoints → Conway Cloud API
- All domain/* endpoints → api.conway.domains (public) or sandbox exec (authenticated)

## Testing: 14 iterations, all 100% pass rate
- Iteration 14: Major refactor — all host operations removed — 17/17 backend, 100% frontend

## Backlog
### P0: Fund Conway credits → full end-to-end provisioning test with real sandbox
### P1: Live dashboard data from sandbox (replace empty defaults with real sandbox queries)
### P2: Smart contracts, Android device control, self-hosted engine
