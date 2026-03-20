# Anima Platform — Changelog

> **NOTE:** Earlier entries reference abandoned naming.
> Current naming: **Anima** (agent), **Anima Machina** (agent framework, CAMEL fork — runs everywhere), **Ultimus** (prediction engine), **Dimensions** (God's-eye view), **Platform** (dashboard+API).
> OpenClaw is NOT the runtime. Anima Machina IS the runtime. See FORK_PROMPT.md.

## 2026-03-20: Step 2 — CAMEL Cloned, Custom Toolkits Built, Agents Working
- Cloned CAMEL-AI (github.com/camel-ai/camel) to /app/anima-machina/ (227MB, 91 toolkits)
- Installed CAMEL as editable package in Python 3.11 environment
- Verified CAMEL ChatAgent works with Emergent Universal Key (gpt-4o-mini via proxy)
- Verified tool calling works (FunctionTool with agent-initiated tool calls)
- Created 3 custom toolkits:
  - WalletToolkit (create_wallet, get_balance, send_payment, get_wallet_info)
  - SpawnToolkit (request_environment, check_environment_status, destroy_environment)
  - StateReportingToolkit (report_state, report_action, report_error, report_financial)
- Registered custom toolkits in camel/toolkits/__init__.py
- Tested StateReportingToolkit e2e: agent pushes state to platform webhook, dashboard receives it
- Tested multi-agent: 3 agents (researcher, trader, coordinator) all reporting to platform simultaneously
- LLM config: Emergent key sk-emergent-... via proxy https://integrations.emergentagent.com/llm/v1


## 2026-03-20: Architecture Pivot — Anima Machina IS the Runtime
- FORK_PROMPT.md completely rewritten with definitive architecture
- Anima Machina (CAMEL fork) is the agent runtime everywhere — NOT OpenClaw
- New concept: Dimensions (God's-eye view for simulation and live modes)
- Multiple Animas can share environments (not 1-VM-per-agent)
- Provisioning must be invisible to users
- 96 skills are for The Catalyst only, not universal starter pack
- All docs updated: ARCHITECTURE.md, ROADMAP.md, PRD.md

## 2026-03-20: Step 1 — Repo Cleanup (PARTIAL)
- Deleted 448MB Conway bloat (automaton/dist, native, node_modules, src, packages)
- Archived 4,100 lines dead code to /app/archive/ (agent_setup, engine_bridge, payment_tracker, sandbox_poller, webhook_daemon)
- Created /app/engine/skills/ (96 custom skills) and /app/engine/templates/ (genesis-prompt, constitution)
- Created thin provision.py (277 lines, replaces 2,457-line agent_setup.py)
- Created providers/base.py (generic BYOI interface) + providers/conway.py
- Rewrote server.py (97 lines, clean imports, no sandbox_poller dependency)
- Updated config.py to point to engine/ instead of automaton/
- Updated agents.py to read skills/templates from engine/
- All docs updated: no MiroFish fork, build Ultimus from scratch on Anima Machina (CAMEL fork)
- Frontend loads, all API endpoints responding, dashboard functional

## 2026-03-20: Documentation Overhaul
- Updated all docs to reflect new architecture: Anima Machina (CAMEL fork) + Ultimus (proprietary)
- Removed all "clone MiroFish" instructions — MiroFish is reference only
- Added NO AGPL rule, Apache-2.0 foundation
- Fixed directory paths (frontend/ and backend/ stay — supervisor locked)
- Made ROADMAP.md the single authoritative task list
- Updated Conway API key in backend/.env to funded key


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
