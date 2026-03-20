# Anima Platform — Changelog

## 2026-03-20: Architecture Blueprint Created
- Created `/app/docs/ARCHITECTURE.md` — complete restructuring plan
- Documented what to KEEP, ARCHIVE, and DELETE
- Defined 4-phase implementation plan
- Defined engine design (runtime.js, wallet.js, tools/)
- Defined target directory structure
- Defined naming/branding (Anima Engine, Anima Tools, Anima Predict, Anima Bridge)

## 2026-03-20: Security Fixes
- Removed ALL platform URL exposure from sandbox exec commands
- Added per-agent webhook tokens (32-byte hex)
- Created SECURITY.md with permanent isolation rules
- Skills/bundle pushed via provider file API (not curl from sandbox)

## 2026-03-19: Genesis Prompt Restored
- Merged 3 historical versions into definitive Anima Fund soul
- WHO YOU ARE (The Catalyst identity)
- PHASE 0 (15 tool tests with REAL usage)
- PHASE 1 (PRIME DIRECTIVE: $5K immediately, no products)
- PHASE 2 ($10K fund launch)
- PHASE 3 (scale organization)
- Anti-stuck rules, self-modification, 50% creator split

## 2026-03-19: Native Addon Fix
- `better_sqlite3.node` always installed via npm inside sandbox
- Never transfer pre-built binaries (corrupt during base64 transfer)
- Added auto-detect + reinstall to `_ensure_system_ready()`

## 2026-03-19: Dashboard Data Pipeline
- genesis.py reads from webhook cache (no direct exec for status)
- engine/logs reads from webhook cache
- engine/live reads from webhook cache
- Infrastructure endpoints connected to real provisioning data

## 2026-03-19: Engine Console
- Added filter buttons: ALL, THINKING, TOOLS, ERRORS, STATE
- Fixed auto-scroll snap to bottom on new logs
- Reads from webhook cache with direct exec fallback

## 2026-03-18: Fly.io Provider
- Created sandbox_provider.py with Conway + Fly.io abstraction
- Fly.io: native /exec API, node:22 image, persistent volume
- Auto-detect existing machines, reuse if found
- Delete Machine button on Genesis screen

## 2026-03-18: Platform-Agent Separation
- Created agent_state.py (centralized MongoDB state)
- All state migrated from filesystem to MongoDB
- deploy_agent reads config from MongoDB (not host env vars)
- create_agent stores in MongoDB only (no host filesystem)

## 2026-03-17: Skills Batching
- 96 skills packed as tar.gz archive (64KB)
- Single download instead of 192 individual API calls
- 10 seconds vs 288 seconds
- Fault-tolerant: failed skills skipped and reported

## 2026-03-11-17: Various
- Deployment readiness (lean requirements.txt: 129→31 packages)
- .gitignore fix (*.env removed, .env files force-tracked)
- Frontend safety timeout (4s max loading state)
- MongoDB connection timeout (5s)
- Conway API key management (per-agent, editable)
- VM tier selector
- Provider selector (Conway/Fly.io)
- 3-screen flow (Genesis → Engine → Dashboard)
- Auto-cascade provisioning steps
- Health check endpoint (probes sandbox, detects provisioning state)
