# Anima Platform — Product Requirements

## Product
A platform to launch, monitor, and manage fully autonomous AI agents (Animas) in sandboxed environments. Users define goals via genesis prompts or Ultimus-generated predictions. Animas operate with full autonomy to achieve those goals.

## Core Components
- **Anima** — autonomous agent instance
- **Anima Machina** — agent framework (CAMEL fork, Apache-2.0). Runs on platform (Ultimus) AND in sandboxed environments (agent runtime). 50+ native toolkits. OpenClaw NOT needed.
- **Ultimus** — prediction/simulation engine built on Anima Machina. CORE product. Three sub-processes: Predictor, Calculator, Executor.
- **Dimensions** — God's-eye view. Observe simulated or live Animas, chat with them, inject variables.
- **Platform** — React dashboard + FastAPI API. Thin control plane. BYOI provisioning.

## User Flows
1. Manual: User creates Anima with custom genesis prompt -> platform provisions -> Anima operates
2. Ultimus: User describes goal -> select predict mode (Quick/Deep/Expert/Iterative) -> Ultimus simulates -> review in Dimensions -> execute -> Anima Machina deploys agents -> platform provisions environments -> Animas operate -> results feed back

## Key Principles
- Animas are fully autonomous (choose tools, strategies, resources)
- Platform is thin (Anima Machina does heavy lifting)
- BYOI is generic (any provider API, not hardcoded list)
- Provisioning is invisible to users
- Multiple Animas can share environments
- Ultimus is core (not optional)
- Predictions are non-linear (thousands of paths simultaneously)
- Genesis prompts auto-generated from simulation data
- 96 custom skills are for The Catalyst ONLY
- Each Anima owns its wallet (private key never leaves sandbox)
- 50% creator revenue split
- NO AGPL code — only Apache-2.0 or proprietary

## Current State (March 2026)
- Step 1 (CLEAN): Partially done. Bloat deleted, assets moved, dead code archived.
- Step 2 (Anima Machina): Not started. CAMEL not yet cloned.
- Step 3 (Platform connection): Not started.
- Step 4 (Ultimus): Not started.
- Step 5 (Multi-Anima + Economics): Not started.
- Dashboard: 14 pages render but show empty data.
- Assets: 96 skills (The Catalyst only), genesis prompt, constitution in engine/.

## Architecture Docs
See /app/docs/ for full details.
FORK_PROMPT.md is the definitive source of truth.
ROADMAP.md is the authoritative task list.
