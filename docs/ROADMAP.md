# Anima Platform — Project Roadmap

## Phase 1: Clean + Restructure (Immediate)
**Goal:** Clean repo, working thin provisioning, one Anima running reliably.

| # | Task | Input | Output | Dependencies |
|---|---|---|---|---|
| 1.1 | Create engine/, ultimus/, archive/ dirs | Current messy repo | New dirs created | None |
| 1.2 | KEEP frontend/ and backend/ | N/A | Supervisor locked — do NOT rename | N/A |
| 1.3 | Archive dead code from backend/ | engine_bridge.py, payment_tracker.py, etc. | archive/ + 1,322 lines removed from backend/ | 1.1 |
| 1.4 | Move skills + templates | automaton/skills/, genesis-prompt.md, constitution.md | engine/skills/, engine/templates/ | 1.1 |
| 1.5 | Delete Conway fork bloat | automaton/dist, native, node_modules, src, packages | 543MB freed | 1.4 |
| 1.6 | Clean backend/ routers | agent_setup.py (2,457L), genesis.py, live.py, etc. | Slim routers: provision.py, monitor.py | 1.3 |
| 1.7 | Update backend/ imports | Old router refs in server.py | Clean server.py with new routers | 1.6 |
| 1.8 | Verify platform loads | Restructured repo | Dashboard renders, API responds | 1.7 |

## Phase 2: Thin Provisioning (Next)
**Goal:** Provision an Anima in 4 commands, not 200+.

| # | Task | Input | Output | Dependencies |
|---|---|---|---|---|
| 2.1 | Write generic BYOI provider interface | sandbox_provider.py reference | providers/base.py — any API | 1.8 |
| 2.2 | Write Conway provider | conway.py reference | providers/conway.py | 2.1 |
| 2.3 | Write provision.py | agent_setup.py reference | ~200 lines: create VM → install OpenClaw → push config → start | 2.1 |
| 2.4 | Write spawn.py | New | Animas request child VMs | 2.3 |
| 2.5 | Test on existing Conway sandbox | Running sandbox | Anima boots with OpenClaw, wallet created, Telegram reports | 2.3 |

## Phase 3: Dashboard Data (Connected)
**Goal:** Every dashboard page shows real data from the running Anima.

| # | Task | Input | Output | Dependencies |
|---|---|---|---|---|
| 3.1 | Research OpenClaw native state output | OpenClaw docs/source | Map of what data is available and where | None |
| 3.2 | Write monitor.py | genesis.py, live.py, infrastructure.py reference | Single router reading OpenClaw state | 3.1 |
| 3.3 | Connect AgentMind page | monitor.py | Live thought stream, engine status, session costs | 3.2 |
| 3.4 | Connect AnimaVM page | monitor.py | Terminal, browser sessions, exec log, filters working | 3.2 |
| 3.5 | Connect Financials page | monitor.py | Revenue, expenses, credits, wallet balance | 3.2 |
| 3.6 | Connect Activity page | monitor.py | Decisions, revenue events, tool calls | 3.2 |
| 3.7 | Connect Infrastructure page | monitor.py | Sandboxes, tools, domains, ports | 3.2 |
| 3.8 | Connect Memory page | monitor.py | Agent's semantic memory | 3.2 |
| 3.9 | Connect OpenClawViewer page | monitor.py | OpenClaw status, browsing sessions | 3.2 |
| 3.10 | Multi-Anima wallet view | spawn.py + monitor.py | All Anima wallets on dashboard | 2.4, 3.2 |
| 3.11 | Full dashboard test | All pages | Every page shows real data | 3.3-3.10 |

## Phase 4: Ultimus (Core Product)
**Goal:** Working prediction engine that generates genesis prompts from simulations.

| # | Task | Input | Output | Dependencies |
|---|---|---|---|---|
| 4.1 | Clone MiroFish + OASIS source | GitHub repos | ultimus/ directory with source | None |
| 4.2 | Full rebrand | MiroFish/OASIS naming | All references → Ultimus | 4.1 |
| 4.3 | Remove external dependencies | External API calls | Self-contained, runs locally | 4.2 |
| 4.4 | Build simulation API | OASIS engine | POST /ultimus/simulate → runs simulation | 4.3 |
| 4.5 | Build GraphRAG integration | CAMEL-AI GraphRAG | Knowledge graph from user's domain data | 4.3 |
| 4.6 | Build report generator | Simulation output | Structured strategy document | 4.4 |
| 4.7 | Build bridge (genesis prompt generator) | Strategy document | N genesis prompts, one per Anima role | 4.6 |
| 4.8 | Build cost calculator | Strategy + pricing data | Seed cost, break-even, projected value | 4.7 |
| 4.9 | Build execute flow | User clicks Launch | Platform provisions Animas with generated prompts | 4.7, 2.3 |
| 4.10 | Build feedback loop | Real execution results | Feed back into Ultimus for next simulation | 4.9 |
| 4.11 | Build Ultimus UI | Ultimus API | New screen in platform: describe goal → simulate → review → execute | 4.4-4.10 |
| 4.12 | Full Ultimus test | End-to-end | Simulate → review → execute → Animas deploy → results feed back | 4.11 |

## Phase 5: Your Network
**Goal:** Agents use your infrastructure and inference.

| # | Task | Input | Output | Dependencies |
|---|---|---|---|---|
| 5.1 | Your infra as BYOI provider | Network SDK | providers/your_network.py | 2.1 |
| 5.2 | Your inference as routing option | Network inference API | Genesis prompt config option | 3.2 |
| 5.3 | Animas deploy nodes on your network | Genesis prompt directive | Anima provisions nodes via SDK | 5.1 |
| 5.4 | Agent-hosted inference | Animas run inference nodes | Other Animas pay via x402 | 5.2, 5.3 |
| 5.5 | Full network test | Ultimus simulation | Simulate network expansion → execute → nodes deploy | 4.12, 5.3 |

## Priority Order
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
(Phase 4 is CORE but needs Phases 1-3 working first)

## Definition of Done (per phase)
- Phase 1: `frontend/` loads, `backend/` API responds, repo is clean, old bloat deleted
- Phase 2: One Anima provisions in <60 seconds on any BYOI provider, wallet shows, Telegram reports
- Phase 3: Every dashboard page shows real data from running Anima
- Phase 4: User describes goal → Ultimus simulates → generates prompts → deploys Animas → results feed back
- Phase 5: Animas deploy nodes on your network, use your inference
