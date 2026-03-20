# Anima Platform — Architecture (Final)

## WHAT THIS IS

A platform to launch, monitor, and manage fully autonomous AI agents (Animas)
in sandboxed environments. Users define goals, the platform provisions
infrastructure, and Animas operate autonomously to achieve those goals.

Ultimus (prediction engine, forked from MiroFish/OASIS) generates goals and
agent definitions from simulations. Users can also create Animas manually.

## NAMING

- **Anima** — an autonomous agent running in its own VM
- **Ultimus** — the prediction/simulation engine (MiroFish/OASIS fork, rebranded)
- **Platform** — the dashboard + API (monitoring, provisioning, agent registry)
- **OpenClaw** — the capability layer installed in each Anima's VM (browser, shell, memory, skills, self-modification)

## THREE LAYERS

### Layer 1: Platform (the control plane)
- Provisions VMs on ANY provider the user connects (BYOI — not a hardcoded list)
- Pushes genesis prompts + config into each Anima's VM
- Monitors all Animas (wallets, state, logs, economics, goal progress)
- Serves the spawn API so Animas can request child VMs
- Tracks every Anima's wallet, parent lineage, and economics
- Hosts Ultimus for simulation-driven deployments

### Layer 2: OpenClaw (capability layer in each VM)
- Browser, shell, memory, self-modification, ClawHub skills, MCP, channels
- The Anima has full flexibility — it CAN make its own decisions on tools,
  skills, inference, and strategy unless the genesis prompt constrains it
- The user decides how much autonomy to give via the genesis prompt

### Layer 3: Anima (the agent)
- Executes goals from its genesis prompt using OpenClaw capabilities
- Has full flexibility to decide HOW to achieve goals unless constrained
- Can spin up child Animas by requesting VMs through the platform's spawn API
- Can write genesis prompts for its children
- Creates its own wallet, manages its own economics
- Reports state back to the platform

## ULTIMUS (Core Product — Not Future)

Ultimus is the prediction/simulation engine. It is CORE to the product.

Flow:
1. User describes a goal ("expand to 3,000 nodes" / "generate $50K DeFi revenue")
2. Ultimus runs simulation with thousands of agent personas
3. Produces: strategy, roles, genesis prompts per role, cost model, confidence scores
4. User reviews, adjusts constraints, clicks Execute
5. Platform provisions Animas with generated genesis prompts
6. Animas operate autonomously to execute the strategy
7. Real results feed back into Ultimus for next iteration

Users can ALSO skip Ultimus and create Animas manually with custom genesis prompts.

## BYOI (Bring Your Own Infrastructure)

The platform provisions VMs on ANY provider the user connects:
- User provides: provider API endpoint + API key + tier preferences
- Platform calls the provider's API to create VMs
- Conway, Fly.io, DigitalOcean, Hetzner, AWS, your own network — anything with an API
- NOT a hardcoded list of providers — the platform adapts to whatever the user brings

When an Anima requests a child VM via the spawn API, the platform uses the
same BYOI config to provision it.

## INFERENCE

The genesis prompt can specify inference constraints or leave it open:
- "Use only GPT-5-mini" → Anima uses only that model
- "Use any model, minimize cost" → Anima picks cheapest available
- "Use our network for inference" → Anima routes to user's inference nodes
- No constraint → Anima decides based on task and wallet balance

The platform provides inference config (available providers, API keys, cost tiers)
as part of the genesis prompt. The Anima uses this config flexibly.

## WHAT EXISTS (March 2026)

### Working:
- Dashboard: 14 pages, 3-screen flow (Genesis → Engine → Dashboard), SSE pipeline
- Agent CRUD: create/select/delete Animas in MongoDB
- Wallet display + QR code (when wallet exists)
- Engine console with logs (from webhook cache)
- Skills listing (146 available)
- Telegram integration
- BYOI provider abstraction (Conway + Fly.io — needs to be generic)
- Security model (SECURITY.md)
- Genesis prompt: The Catalyst soul (restored, 271 lines)
- Constitution: ethical framework
- 96 custom skills

### Broken / Bloated:
- Provisioning: 2,457 lines making 200+ API calls (should be ~200 lines, 4 calls)
- Conway engine fork: 543MB, crashes constantly (replace with OpenClaw)
- Data pipeline: reads JSON files that don't exist (connect to OpenClaw native state)
- Dead code: engine_bridge.py (1,108L), payment_tracker.py (142L), webhook_daemon_template.py (72L)
- Dashboard pages mostly empty (data pipeline broken)

### Not Yet Built:
- Ultimus (MiroFish/OASIS fork — core product, must build)
- Generic BYOI (currently hardcoded to Conway + Fly.io)
- Multi-Anima tracking (parent-child relationships, all wallets)
- Spawn API (Animas request child VMs through platform)
- Your network as BYOI provider + inference provider

## TASK LIST

See **ROADMAP.md** for the authoritative task list and phase definitions.

## REPO STRUCTURE (Target)

**NOTE: Supervisor config is READONLY. frontend/ and backend/ paths cannot be renamed.**

```
/app
├── frontend/           ← Dashboard (KEEP — supervisor locked)
│   └── src/pages/     ← 14 dashboard pages
│
├── backend/            ← Platform API (KEEP — supervisor locked)
│   ├── routers/
│   │   ├── agents.py      ← Anima CRUD
│   │   ├── provision.py   ← Thin launcher (~200 lines)
│   │   ├── monitor.py     ← Read Anima state
│   │   ├── spawn.py       ← Child VM requests from Animas
│   │   ├── telegram.py    ← Telegram integration
│   │   └── webhooks.py    ← Receive Anima state reports
│   └── providers/
│       └── base.py        ← Generic BYOI interface
│
├── engine/             ← What gets installed in each VM
│   ├── skills/        ← 96 custom skills
│   └── templates/     ← Genesis prompts, constitution
│
├── ultimus/            ← Prediction engine (MiroFish/OASIS fork)
│   ├── simulation/    ← Simulation runner
│   ├── bridge/        ← Simulation → genesis prompt converter
│   └── knowledge/     ← GraphRAG ontologies
│
├── archive/            ← Reference from old codebase
└── docs/               ← Architecture, security, changelog
```

## CRITICAL RULES
1. Platform is THIN — OpenClaw does heavy lifting inside VMs
2. Animas have flexible autonomy — user decides constraints via genesis prompt
3. BYOI is GENERIC — any provider with an API, not a hardcoded list
4. Ultimus is CORE — not a future add-on
5. NEVER expose platform internals to the sandbox (SECURITY.md)
6. Each Anima owns its private key — never transmitted
7. The genesis prompt is sacred — The Catalyst soul must not be stripped again
8. 96 custom skills are YOUR IP
