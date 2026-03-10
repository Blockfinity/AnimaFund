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
- **Seed Funding**: ~$10 total ($5 VM + $5 credits). Agent must earn to survive.
- **Sandbox compute**: Small VM ($5/mo) — paid from Conway API key credits
- **Agent wallet**: Created INSIDE sandbox by Conway Terminal (step 2 of provisioning)
- **Agent wallet used for**: x402 payments (domains, paid APIs, services, self-funding credits)
- **Self-sustaining**: Agent can buy its own credits via x402_fetch to /v1/credits/purchase

## Onboarding Flow
1. Open app → Genesis screen with credits funding panel + 6-step provisioning stepper
2. **Step 0: Fund Conway Credits** — Select tier ($5-$2500), get QR code for USDC on Base payment
3. Create Sandbox (requires $25+ credits) → Install Terminal (wallet created here) → Install OpenClaw → Claude Code → Load Skills → Create Anima
4. After wallet created → QR code displayed for agent wallet funding
5. After Create Anima → "Open Dashboard" button
6. Dashboard → AnimaVM monitoring page (status bar + 7 tabs)

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
- `GET /api/credits/balance` → Conway credit balance for API key
- `GET /api/credits/pricing` → VM pricing tiers and credit purchase tiers
- `POST /api/credits/purchase` → x402 payment details (QR code, USDC address, amount)
- All provision/* endpoints → Conway Cloud API
- All domain/* endpoints → api.conway.domains (public) or sandbox exec (authenticated)

## Testing: 18 iterations, all 100% pass rate
- Iteration 16: Comprehensive pre-deployment E2E — 21/21 backend, Telegram confirmed, deployment PASS
- Iteration 17: Sandbox management & credit preservation — 11/11 backend, all frontend verified
- Iteration 18: Real-time data pipeline E2E — 12/12 backend, all frontend SSE-driven data verified

## Completed (Mar 10 2026)
### Conway Credits Funding Mechanism (P0)
- Created `/app/backend/routers/credits.py` with 3 endpoints (balance, pricing, purchase)
- Frontend: Credits panel on genesis screen with tier selector, QR code, payment instructions
- x402 protocol integration: Conway returns USDC payment address on Base network

### Sandbox Credit Preservation
- create-sandbox checks Conway API for existing sandboxes and reuses them (no duplicate charges)
- delete-sandbox blocked — Conway sandboxes are prepaid and non-refundable
- New reset-sandbox endpoint: wipes agent data, kills processes, resets provisioning, keeps VM alive
- Sandbox IDs persisted in MongoDB for durability
- Frontend: "Reset Agent" button (visible only when sandbox exists) with confirmation dialog

### Agent Self-Funding Survival Protocol (P1)
- Updated `genesis-prompt.md` with SURVIVAL section: credits = existence
- Agent monitors credits every turn, calculates runway (hours remaining)
- Self-funding via x402_fetch to Conway purchase endpoint using its own USDC wallet
- Survival tiers (NORMAL → CONSERVATION → SURVIVAL → CRITICAL → EMERGENCY)
- Auto-buy protocol: wallet > $5 AND credits < $3 → buy $5 credits
- Telegram alerts to creator when credits drop below $2

### Cost-Aware Survival Overhaul (P1)
- Replaced rigid cost tables with live query instructions (credits_balance, credits_pricing, x402_check)
- Agent checks costs in real-time from Conway API, not hardcoded values
- Resources scale with earnings — start small VM, upgrade as revenue grows
- 50% creator split enforced with tracking in creator-split-log.json
- Decision framework: fast, not fearful — take calculated risks, don't overthink pennies
- Survival section trimmed: top up credits from wallet, alert creator if both are empty, never stop
- Phase 1 rewritten as aggressive revenue-focused with scaling mindset
- Changed default VM from X-Large ($25/mo) to Small ($5/mo) — matching seed funding
- Updated frontend: $5 minimum threshold, $5 default tier, survival messaging

### Real-Time Data Pipeline (P0 — Completed Mar 10 2026)
- Webhook-driven architecture: sandbox daemon POSTs to `/api/webhook/agent-update`
- `sandbox_poller.py`: Server-side cache + `asyncio.Event` for instant SSE notification
- SSE stream at `/api/live/stream`: pushes data the instant a webhook arrives (~1.9s latency)
- Falls back to 20s polling if webhooks stop (when sandbox is active)
- All `/api/live/*` endpoints now read from webhook cache (financials, activity, soul, heartbeat, turns, memory)
- Frontend `AnimaVM.js`: SSE consumer drives status bar (Credits, Phase, Earned, Turns, LIVE indicator)
- Bug fixes: `last_poll` → `last_update` field mismatch in AnimaVM.js + live.py heartbeat, added missing `Loader2` import
- E2E verified: webhook→cache→SSE→frontend flow works with instant push

## Backlog
### P1: Implement Real Smart Contracts
### P2: Android device control, self-hosted agent engine
