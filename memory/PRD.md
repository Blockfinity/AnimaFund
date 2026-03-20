# Anima Platform — Product Requirements

## Product
A platform to launch, monitor, and manage fully autonomous AI agents (Animas) in sandboxed environments. Users define goals via genesis prompts or Ultimus-generated predictions. Animas operate with full autonomy to achieve those goals.

## Core Components
- **Anima** — autonomous agent in its own VM with OpenClaw capabilities
- **Anima Machina** — agent framework (forked from CAMEL, Apache-2.0, proprietary modifications)
- **Ultimus** — prediction/simulation engine (built from scratch on Anima Machina, proprietary). CORE product, not future.
- **Platform** — dashboard + API. Provisions VMs, monitors Animas, serves spawn API.
- **OpenClaw** — capability layer in each VM. Browser, shell, memory, skills, self-modification. Installed as-is, not forked.
- **BYOI** — any VM provider with an API. Not a hardcoded list.

## User Flows
1. Manual: User creates Anima with custom genesis prompt -> platform provisions -> Anima operates
2. Ultimus: User describes goal -> Ultimus simulates (Quick/Deep/Expert/Iterative) -> generates genesis prompts -> user executes -> platform provisions Animas -> they operate -> results feed back to Ultimus

## Key Principles
- Animas have flexible autonomy (user decides constraints via genesis prompt)
- Platform is thin (OpenClaw does heavy lifting)
- BYOI is generic (any provider)
- Ultimus is core (not optional)
- Each Anima owns its wallet (private key never leaves VM)
- 50% creator revenue split
- NO AGPL code anywhere — only Apache-2.0 (CAMEL/Anima Machina) or proprietary
- MiroFish is REFERENCE ONLY (study workflow, don't copy code)

## Current State (March 2026)
- Dashboard: 14 pages, 40% functional
- Provisioning: broken (2,457 lines, needs ~200)
- Agent runtime: Conway fork, crashes (replacing with OpenClaw)
- Anima Machina: not yet cloned
- Ultimus: not yet built
- Assets: 96 skills, The Catalyst genesis prompt, constitution, BYOI abstraction

## Architecture Docs
See /app/docs/ for full architecture, roadmap, and security docs.
ROADMAP.md is the single authoritative task list with phase definitions.
