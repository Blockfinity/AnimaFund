# Anima Platform — Product Requirements

## Product
A platform to launch, monitor, and manage fully autonomous AI agents (Animas) in sandboxed environments. Users define goals via genesis prompts or Ultimus-generated predictions. Animas operate with full autonomy to achieve those goals.

## Core Components
- **Anima** — autonomous agent instance
- **Anima Machina** — agent framework (CAMEL fork, Apache-2.0). Runs on platform (Ultimus) AND in sandboxed environments (agent runtime). 50+ native toolkits + 3 custom (Wallet, Spawn, StateReporting). OpenClaw NOT needed.
- **Ultimus** — prediction/simulation engine built on Anima Machina. CORE product. Three sub-processes: Predictor, Calculator, Executor.
- **Dimensions** — God's-eye view. Observe simulated or live Animas, chat with them, inject variables.
- **Platform** — React dashboard + FastAPI API. Thin control plane. BYOI provisioning.

## Current State (March 2026)

### Completed
- Step 1 (CLEAN): Bloat deleted, assets moved to engine/, dead code archived
- Step 2 (CAMEL CLONE): CAMEL cloned to /app/anima-machina/, 3 custom toolkits built, agents working with Emergent key, multi-agent tested, state reporting to platform webhook verified

### Next: Step 2 completion
- Connect platform server.py to import/initialize Anima Machina agents
- Connect dashboard pages to Anima Machina state data (via webhook cache)
- Rebrand: camel -> anima_machina across codebase

### Upcoming
- Step 3: Connect Platform to Anima Machina (generic BYOI provisioning, monitor.py, dashboard pages)
- Step 4: Build Ultimus (predictor, calculator, executor, Dimensions, 4 seed data modes)
- Step 5: Multi-Anima + Economics (spawn API, treasury, wallet/x402)
- Step 6: Your Network

## Architecture Docs
See /app/docs/ for full details.
FORK_PROMPT.md is the definitive source of truth.
ROADMAP.md is the authoritative task list.
