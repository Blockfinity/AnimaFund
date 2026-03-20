# Anima Platform — Complete Build Assessment

## WHAT WE HAVE vs WHAT WE NEED

### Platform Dashboard (Frontend) — 60% Complete
| Page | Lines | Status | What's Missing |
|---|---|---|---|
| App.js (3 screens) | ~1050 | Working | Genesis redirect bug fixed, engine screen 10% smaller |
| AgentMind | 832 | Partially working | Engine status shows OFFLINE, session costs all zero |
| AnimaVM | 880 | Mostly broken | Filters don't work, all sections empty, no terminal embed |
| FundHQ | 594 | Scaffold only | Shows structure but no real data |
| Infrastructure | 480 | Partially connected | Now reads from provisioning, but most data empty |
| Skills | 338 | Working | Lists 146 skills correctly |
| Financials | 206 | Empty | Reads from cache but agent doesn't write economics.json |
| Agents | 192 | Working | CRUD works, agent list works |
| Activity | 148 | Empty | No activity data from agent |
| Memory | 143 | Empty | Agent memory not connected |
| Configuration | 119 | Basic | Shows config but no edit |
| OpenClawViewer | 559 | Not working | Depends on OpenClaw endpoints that return empty |
| DealFlow | 57 | Scaffold only | Placeholder |
| Portfolio | 57 | Scaffold only | Placeholder |
| **Total frontend** | **~6,500** | **~40% functional** | |

### Platform API (Backend) — 50% Complete
| File | Lines | Status | What's Missing |
|---|---|---|---|
| agent_setup.py | 2,457 | Bloated, fragile | Should be ~200 lines. 200+ API calls for 6 operations |
| agents.py | 384 | Working | Agent CRUD, skills listing |
| genesis.py | 357 | Partially working | Reads from webhook cache, but cache often empty |
| sandbox_provider.py | 344 | Working | Conway + Fly.io abstraction |
| sandbox_poller.py | 321 | Fragile | Polls sandbox but reads JSON files that don't exist |
| live.py | 306 | Partially working | SSE stream works but data often empty |
| credits.py | 262 | Working | Conway credits management |
| telegram.py | 159 | Working | Telegram bot integration |
| agent_state.py | 157 | Working | MongoDB state management |
| conway.py | 175 | Working | Conway API proxy |
| infrastructure.py | 111 | Basic | Reads from provisioning |
| server.py | 113 | Working | FastAPI + startup |
| webhook.py | 41 | Working | Webhook receiver with auth |
| engine_bridge.py | 1,108 | DEAD CODE | Reads Conway state.db locally |
| payment_tracker.py | 142 | DEAD CODE | Depends on engine_bridge |
| **Total backend** | **~7,100** | **~40% functional** | |

### Agent Runtime (Automaton/Conway Fork) — TO BE REPLACED
| Component | Status | Replacement |
|---|---|---|
| bundle.mjs (10MB) | Conway-dependent, breaks constantly | Fork OpenClaw as Anima Engine |
| better_sqlite3.node | Corrupts during transfer | Ships inside OpenClaw |
| 96 custom skills | YOUR IP, keep | Load into Anima Engine |
| genesis-prompt.md | Restored (The Catalyst) | Keep, push to agent at deploy |
| constitution.md | Working | Keep |
| Conway Terminal | Unnecessary middleman | Eliminated |
| Conway Compute | Vendor lock-in | Direct LLM APIs + smart routing |
| Conway Credits | Vendor lock-in | x402 (Coinbase open protocol) |

---

## WHAT NEEDS TO BE BUILT

### Phase 1: Restructure + Thin Launcher (Working platform with OpenClaw agent)
**Goal:** One agent running reliably on any VM, all dashboard pages showing real data.

| Task | Description | Effort | Priority |
|---|---|---|---|
| 1.1 Restructure repo | Clean backend/, create engine/, archive bloat | 1 session | P0 |
| 1.2 Fork OpenClaw | Clone repo, rebrand, add to engine/ | 1 session | P0 |
| 1.3 Add wallet + x402 to OpenClaw fork | ethers.js wallet generation + x402 client | 1-2 sessions | P0 |
| 1.4 Add state reporting | Agent pushes state to platform webhook (built into runtime) | 1 session | P0 |
| 1.5 Rewrite provision.py | Thin launcher: create VM, push OpenClaw + config, start | 1 session | P0 |
| 1.6 Build agent Docker image | OpenClaw + wallet + skills + genesis prompt in one image | 1 session | P0 |
| 1.7 Fix AnimaVM page | Connect to real sandbox terminal, fix filters | 1 session | P1 |
| 1.8 Fix AgentMind page | Engine status from real data, session costs | 1 session | P1 |
| 1.9 Fix Financials page | Read from agent's economics data | 1 session | P1 |
| 1.10 Fix Activity page | Connect to agent's decision/revenue logs | 1 session | P1 |
| 1.11 Fix Memory page | Connect to agent's semantic memory | 1 session | P1 |
| 1.12 Fix OpenClawViewer | Show real OpenClaw status and browsing sessions | 1 session | P1 |
| 1.13 End-to-end test | One agent, full provisioning, all dashboard pages | 1 session | P0 |
| **Phase 1 Total** | | **~13 sessions** | |

### Phase 2: Agent Capabilities (Fully autonomous agent)
**Goal:** Agent earns revenue, manages wallet, spawns children, self-modifies.

| Task | Description | Effort | Priority |
|---|---|---|---|
| 2.1 Integrate x402 payments | Agent can pay for services and charge for services via USDC | 2 sessions | P0 |
| 2.2 Add Treasurer capability | Budget management, fund child agents, collect revenue | 2 sessions | P0 |
| 2.3 Add spawn_child via platform | Agent calls platform API to create child VMs | 2 sessions | P0 |
| 2.4 Modular inference routing | Agent picks model based on task importance × wallet balance | 1 session | P1 |
| 2.5 Self-hosted inference option | Ollama/vLLM integration for zero-cost survival mode | 1 session | P2 |
| 2.6 Agent lifecycle management | Health monitoring, productivity scoring, auto-termination | 2 sessions | P1 |
| 2.7 Per-node Treasurer model | Each node of agents has its own budget manager | 2 sessions | P1 |
| 2.8 ClawHub integration | Agent discovers and installs skills autonomously | 1 session | P0 |
| 2.9 Domain management | Agent registers/manages domains via registrar API | 1 session | P2 |
| 2.10 Full e2e autonomous test | Agent boots, earns, spawns child, child earns, reports | 2 sessions | P0 |
| **Phase 2 Total** | | **~16 sessions** | |

### Phase 3: Prediction Layer (Simulation → Execution)
**Goal:** Simulate scenarios, calculate costs, one-click deploy agent swarms. Built from scratch on Anima Machina (CAMEL fork). NO MiroFish/OASIS code.

| Task | Description | Effort | Priority |
|---|---|---|---|
| 3.1 Clone CAMEL → Anima Machina | Clone github.com/camel-ai/camel, rebrand as Anima Machina | 1 session | P0 |
| 3.2 Build GraphRAG integration | Knowledge graph from your domain data (via Anima Machina GraphRAG) | 2 sessions | P1 |
| 3.3 Build simulation→execution bridge | Convert simulation outcomes to genesis prompts + cost model (YOUR IP) | 3 sessions | P0 |
| 3.4 Build cost calculator UI | Show seed cost, break-even, projected value before launch (YOUR IP) | 1 session | P0 |
| 3.5 Build Network Treasurer | Seeds first wave, monitors expansion, reports | 2 sessions | P0 |
| 3.6 Build wave deployment system | Automatic agent deployment as revenue thresholds are met | 2 sessions | P0 |
| 3.7 Build feedback loop | Real execution results feed back into simulation (YOUR IP) | 2 sessions | P1 |
| 3.8 Build 4 seed data modes | Quick/Deep/Expert/Iterative predict modes | 2 sessions | P0 |
| 3.9 Full simulation→execution test | Simulate 100 agents → calculate → seed 10 → propagate | 2 sessions | P0 |
| **Phase 3 Total** | | **~17 sessions** | |

### Phase 4: Your Network (Agents deploy nodes autonomously)
**Goal:** Agents provision and manage nodes on your infrastructure.

| Task | Description | Effort | Priority |
|---|---|---|---|
| 4.1 Build network SDK | API for agents to deploy/manage nodes | 3 sessions | P0 |
| 4.2 Add provision.js tool to engine | Agent can call SDK to deploy nodes | 1 session | P0 |
| 4.3 Build node health monitoring | Dashboard shows node status across network | 2 sessions | P1 |
| 4.4 Build agent-hosted inference | Agents run inference nodes, charge other agents via x402 | 3 sessions | P1 |
| 4.5 Full network test | Agent deploys 10 nodes, monitors, scales | 2 sessions | P0 |
| **Phase 4 Total** | | **~11 sessions** | |

---

## TOTAL EFFORT ESTIMATE

| Phase | Sessions | Calendar Time (1 session/day) | Description |
|---|---|---|---|
| Phase 1 | ~13 | ~2 weeks | Working platform + reliable agent |
| Phase 2 | ~16 | ~2.5 weeks | Fully autonomous agent with payments |
| Phase 3 | ~15 | ~2.5 weeks | Prediction → execution engine |
| Phase 4 | ~11 | ~2 weeks | Your network integration |
| **TOTAL** | **~55 sessions** | **~9 weeks** | |

### Emergent Credit Estimate
Based on current usage patterns:
- Average session: ~$15-25 of Emergent credits (varies by complexity)
- Phase 1 (13 sessions): ~$200-325
- Phase 2 (16 sessions): ~$240-400
- Phase 3 (15 sessions): ~$225-375
- Phase 4 (11 sessions): ~$165-275
- **Total estimate: ~$830-1,375 in Emergent credits**
- **With testing/debugging overhead (30%): ~$1,080-1,790**

### What You Get at Each Phase

**After Phase 1 ($200-325):**
- Working platform with real data on all dashboard pages
- One agent running reliably on any VM
- Agent has full OpenClaw capabilities (browser, shell, memory, self-modification)
- ClawHub access for skill discovery
- Telegram reporting working
- BYOI: Conway, Fly.io, Docker, any VPS

**After Phase 2 ($440-725 cumulative):**
- Agent earns revenue autonomously via x402
- Agent spawns and manages child agents
- Per-node Treasurer manages budgets
- Agent picks cheapest inference based on wallet balance
- Unproductive agents auto-terminated
- The Catalyst is fully operational

**After Phase 3 ($665-1,100 cumulative):**
- Simulate any scenario with thousands of agents
- Cost calculator shows seed funding needed
- One-click deploys agent swarms
- Agents self-propagate to target network size
- **This is your unique IP — nobody else has simulation→execution**

**After Phase 4 ($830-1,375 cumulative):**
- Agents deploy nodes on your network autonomously
- Agent-hosted inference (agents serve other agents)
- Full self-sustaining agent economy
- **First-to-market autonomous node deployment**

---

## WHAT WE KEEP FROM CURRENT CODEBASE

| Asset | Value | Location |
|---|---|---|
| 14 dashboard pages | Weeks of UI work | frontend/src/pages/ |
| 4 components (Header, Sidebar, EngineConsole, CreateAgentModal) | Core UI | frontend/src/components/ |
| SSE hooks (useSSE, useSSETrigger) | Real-time data pipeline | frontend/src/hooks/ |
| 3-screen flow (Genesis → Engine → Dashboard) | Core UX | frontend/src/App.js |
| 96 custom skills | YOUR IP | engine/skills/ |
| Genesis prompt (The Catalyst) | Agent soul | engine/templates/ |
| Constitution | Ethical framework | engine/templates/ |
| Agent CRUD + MongoDB state | Core data layer | backend/routers/agents.py, backend/agent_state.py |
| BYOI provider abstraction | Multi-provider support | backend/providers/ |
| Telegram integration | Agent reporting | backend/routers/telegram.py |
| Security model | Agent isolation rules | docs/SECURITY.md |
| Architecture blueprint | Complete plan | docs/ARCHITECTURE.md |

## WHAT WE DELETE

| Asset | Why |
|---|---|
| automaton/node_modules (427MB) | Conway dependencies |
| automaton/dist/bundle.mjs (10MB) | Conway engine, replaced by OpenClaw fork |
| automaton/native (5.8MB) | Pre-built binaries that corrupt |
| automaton/src (2.4MB) | Conway TypeScript source |
| agent_setup.py (2,457L) | Bloated provisioning, rewrite as ~200L |
| engine_bridge.py (1,108L) | Dead code |
| payment_tracker.py (142L) | Dead code |
| sandbox_poller.py (321L) | Fragile, replace with agent-side reporting |
| webhook_daemon_template.py | External daemon that dies, replace with built-in reporting |
