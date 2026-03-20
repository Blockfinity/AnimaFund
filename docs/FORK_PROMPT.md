# FORK PROMPT — READ THIS ENTIRE DOCUMENT BEFORE WRITING ANY CODE

## WHAT IS ANIMA

A platform to launch, monitor, and manage fully autonomous AI agents (Animas) in sandboxed environments. Users define goals either manually or through Ultimus (prediction engine). Animas operate with full autonomy to achieve those goals — choosing their own tools, strategies, and resources. They can spawn child Animas, earn revenue, pay for their own compute, and self-modify.

## NAMING (use these EVERYWHERE — no exceptions)
- **Anima** — an individual autonomous agent
- **Anima Machina** — the agent framework (forked from CAMEL-AI, Apache-2.0, fully rebranded). Runs BOTH on the platform (for Ultimus simulations) AND inside sandboxed environments (as the agent runtime). Has 50+ native toolkits.
- **Ultimus** — the prediction/simulation engine. Built on Anima Machina. Separate system. Dashboard screens, not a separate app.
- **Dimensions** — the God's-eye view. Observe simulated or live Animas, chat with them, inject variables. Dashboard screens.
- **Platform** — the React dashboard + FastAPI API. Thin control plane.

## ARCHITECTURE — THREE SEPARATE SYSTEMS

### 1. Anima Machina (the agent framework — CAMEL fork)
Creates agents. Runs them. Gives them tools, memory, personas, inference. Runs EVERYWHERE:
- On the platform server: powers Ultimus simulations (thousands of personas in one process)
- Inside sandboxed environments: each Anima is an Anima Machina agent instance with its own genesis prompt, tools, memory

CAMEL natively has 50+ toolkits: BrowserToolkit, TerminalToolkit, CodeExecutionToolkit, FileWriteTool, TwitterToolkit, LinkedInToolkit, RedditToolkit, SlackToolkit, WhatsAppToolkit, GitHubToolkit, SearchToolkit, StripeToolkit, OpenBBToolkit, GoogleCalendarToolkit, IMAPMailToolkit, MCPToolkit, MemoryToolkit, ImageAnalysisToolkit, VideoAnalysisToolkit, AudioAnalysisToolkit, NotionToolkit, ZapierToolkit, GoogleMapsToolkit, plus custom tools from any Python function via FunctionTool.

OpenClaw is NOT needed as a runtime. Anima Machina has all capabilities natively. If an Anima decides it wants OpenClaw or PicoClaw for something, it installs it itself.

What we ADD to CAMEL to make it Anima Machina:
- Wallet toolkit (web3.py for USDC management, x402 for payments)
- Spawn toolkit (request new sandboxed environments from the platform API)
- State reporting toolkit (push agent state to platform webhook)
- Full rebrand (all "camel" references -> "anima_machina")
- Remove telemetry, CAMEL-specific branding, modules we don't use

CAMEL does NOT natively isolate agents. All agents run in one Python process. The PLATFORM handles isolation by provisioning separate sandboxed environments via BYOI.

### 2. Ultimus (prediction engine — built on Anima Machina, NOT forked from MiroFish)
Completely separate from Anima Machina. Uses Anima Machina's capabilities but is its own system.

Ultimus has THREE sub-processes:
- **Predictor**: Simulates scenarios with thousands of personas. Non-linear. Multi-step cause-and-effect. Explores ALL paths simultaneously (not linear). Each persona has: personality, long-term memory, behavioral logic, social relationships, action capabilities.
- **Calculator**: Takes prediction output, computes infrastructure needs, costs, timeline, feasibility. Does NOT reject predictions — if resources are limited, it simulates how to achieve the goal with less, or what earning strategies are needed first.
- **Executor**: Hands agent specs to Anima Machina for deployment. Anima Machina creates the agents, the platform provisions the environments. Invisible to the user.

Seed data modes (build all four):
- Quick Predict: goal description only, LLM-generated personas
- Deep Predict: platform auto-researches domain via web search
- Expert Predict: user uploads documents, GraphRAG builds knowledge graph
- Iterative Predict: starts quick, identifies gaps, auto-researches, re-runs

When user clicks Execute: each simulated persona's behavioral history becomes the blueprint for a real Anima. The genesis prompt is generated from the simulation data — not a template. It contains the specific actions, strategies, relationships, and triggers that the simulation showed work.

Ultimus is dashboard SCREENS, not a separate app. Goal input, simulation progress, Dimensions (simulation mode), cost review, execute button — all React pages in the existing dashboard.

MiroFish (https://github.com/666ghj/MiroFish/blob/main/README-EN.md) is REFERENCE ONLY. Study its workflow (seed -> GraphRAG -> personas -> simulation -> report -> God's-eye view). Do NOT copy its code. It's Chinese, AGPL, depends on Zep Cloud. Ultimus is built from scratch on Anima Machina (Apache-2.0, proprietary).

After Ultimus is built, there must be ZERO references to MiroFish, OASIS, CAMEL, or "fish" in any code or docs. Only exception: anima-machina/LICENSE and anima-machina/NOTICE for Apache-2.0 legal attribution.

### 3. Platform (thin control plane)
- Provisions sandboxed environments via BYOI (any provider API — user provides endpoint + key once in settings, then everything is automatic and invisible)
- Monitors all Animas (wallets, state, logs, economics, goal progress)
- Provides spawn API (Animas request new environments through the platform)
- Provides Dimensions (live mode — observe real Animas, chat with them, intervene)
- Kill switch (destroy any Anima's environment instantly)
- Dashboard with existing 14 pages + new Ultimus/Dimensions screens

## CRITICAL PRINCIPLES — DO NOT VIOLATE

1. **Animas are fully autonomous within their genesis prompt.** They choose tools, strategies, skills, resources. The platform doesn't prescribe runtimes or force schedules.
2. **BYOI is generic.** The user provides ANY provider's API endpoint and key. The platform provisions on it. Not a hardcoded list of Conway/Fly/Docker.
3. **Provisioning is invisible.** The user never sees "creating VM... installing tools..." They see "Executing prediction... Animas deploying..."
4. **Multiple Animas can share environments or have dedicated ones.** Flexible, based on what the task requires. NOT one-VM-per-agent.
5. **All Animas are sandboxed.** The platform can kill any environment at any time. Animas cannot escape their sandbox or access other Animas' data.
6. **Every prediction must be self-sustaining.** Seed capital starts it. Animas earn to cover costs and expand. If resources are limited, the prediction adapts — it doesn't get rejected.
7. **Predictions are non-linear.** Thousands of paths explored simultaneously. 100 predicted steps might resolve in 1 real action. The genesis prompt contains intent and strategy, not rigid scripts.
8. **Genesis prompts are auto-generated.** Ultimus produces them from simulation data. Manual creation is also supported but the system is designed for automated generation at scale.
9. **The 96 custom skills are for The Catalyst (Anima Fund) ONLY.** Not a universal starter pack. Each Anima gets skills specific to its role from the prediction or user specification.
10. **Ultimus and Anima Machina are SEPARATE systems.** Ultimus predicts. Anima Machina creates/deploys agents. Clean boundary. They communicate through APIs.

## CURRENT STATE OF THE CODEBASE (verified March 20 2026)

### Partially cleaned (Phase 1 started, not complete):
```
/app
├── automaton/          <- Conway fork. Bloat deleted (dist, native, node_modules, src, packages).
│                          skills/ and genesis-prompt.md still here (copied to engine/).
├── backend/            <- FastAPI API. Supervisor locked to this path.
│   ├── routers/
│   │   ├── agents.py        <- 384 lines. Agent CRUD. WORKS. KEEP.
│   │   ├── conway.py        <- 175 lines. Conway-specific. REPLACE with generic BYOI.
│   │   ├── credits.py       <- 262 lines. Conway credits. Keep as optional provider feature.
│   │   ├── genesis.py       <- 357 lines. Reads from stub cache. REWRITE to read from Anima Machina.
│   │   ├── infrastructure.py <- 111 lines. Basic stubs. REWRITE.
│   │   ├── live.py          <- 306 lines. SSE stream. KEEP but connect to real data.
│   │   ├── openclaw.py      <- 364 lines. OpenClaw-specific. EVALUATE — may not be needed.
│   │   ├── provision.py     <- 277 lines. New thin provisioning. Conway assumptions baked in. REWRITE to be truly generic.
│   │   ├── telegram.py      <- 159 lines. WORKS. KEEP.
│   │   └── webhook.py       <- 41 lines. WORKS. KEEP.
│   ├── providers/
│   │   ├── __init__.py      <- BaseProvider ABC. KEEP.
│   │   └── conway.py        <- Conway provider impl. KEEP behind BYOI interface.
│   ├── sandbox_poller.py    <- Stub (39 lines). genesis.py/live.py depend on it. Will be eliminated when those are rewritten.
│   ├── agent_state.py       <- 157 lines. MongoDB state. KEEP.
│   ├── database.py          <- 35 lines. MongoDB connection. KEEP.
│   ├── config.py            <- 18 lines. Points to engine/. KEEP.
│   ├── server.py            <- 97 lines. Clean. KEEP and update as routers change.
│   └── telegram_notify.py   <- 192 lines. KEEP.
├── engine/             <- Created. Has skills/ (96) and templates/ (genesis-prompt, constitution).
├── archive/            <- Created. Has old agent_setup.py, engine_bridge.py, etc.
├── frontend/           <- React dashboard. Supervisor locked. Add Ultimus/Dimensions screens.
├── docs/               <- Architecture docs. Need updating with this document.
├── memory/PRD.md       <- Product requirements. Need updating.
└── (anima-machina/ and ultimus/ need to be CREATED)
```

### What works:
- Frontend renders 14 pages with SSE pipeline (showing empty data — connected to stub cache)
- Agent CRUD in MongoDB
- Telegram integration
- Webhook receiver
- Conway sandbox is running with live agent (wallet 0x922868..., engine_running: True)
- Genesis prompt (The Catalyst, 271 lines) in engine/templates/genesis-prompt.md
- 96 custom skills in engine/skills/
- Constitution in engine/templates/constitution.md
- All API endpoints responding (health, agents, skills, provision, webhook, payments)

### What doesn't work:
- Dashboard pages show empty data (connected to stub cache)
- Provisioning has Conway assumptions baked in (not truly generic BYOI)
- No Anima Machina (not cloned yet)
- No Ultimus (not built yet)
- No wallet/x402
- No spawn API
- No Dimensions

## WHAT TO DO — IN ORDER

### Step 1: FINISH CLEAN (partially done)
- Delete sandbox_provider.py (Conway-specific, replaced by providers/)
- Clean up remaining automaton/ files (keep originals as backup, engine/ has the copies)
- Create anima-machina/ directory (placeholder for Step 2)
- Verify: backend starts, frontend loads, all endpoints respond

### Step 2: CLONE CAMEL -> ANIMA MACHINA
- git clone https://github.com/camel-ai/camel /app/anima-machina/
- Full rebrand: all "camel" references -> "anima_machina" in module names, imports, configs, docs, API endpoints, env vars, logs
- Keep Apache-2.0 LICENSE and add NOTICE file (legal requirement)
- Remove telemetry/analytics
- Remove modules not needed for our use case
- Add wallet toolkit (web3.py + x402)
- Add spawn toolkit (calls platform API to request new environments)
- Add state reporting toolkit (pushes agent state to platform webhook)
- Test: create an Anima Machina agent on the platform server, give it BrowserToolkit + TerminalToolkit, have it browse a website and run a shell command

### Step 3: CONNECT PLATFORM TO ANIMA MACHINA
- Rewrite provisioning: generic BYOI provider interface -> create environment -> install Anima Machina runtime -> push genesis prompt + config -> start. ~200 lines max. Invisible to user.
- Rewrite monitor.py: read agent state from Anima Machina (not dead cache). One router replacing genesis.py + live.py + infrastructure.py.
- Connect each dashboard page to real Anima Machina data
- Connect SSE pipeline to Anima Machina state updates
- Test: deploy Anima Machina agents into sandboxed environment, verify ALL dashboard pages show real data

### Step 4: BUILD ULTIMUS
- Predictor, Calculator, Executor sub-processes
- Dimensions (God's-eye view — simulation and live modes)
- All 4 seed data modes (Quick/Deep/Expert/Iterative Predict)
- Frontend screens in existing dashboard
- Reference MiroFish README-EN for workflow concepts ONLY
- Test: describe goal -> simulate -> review in Dimensions -> execute -> real Animas deploy -> results feed back

### Step 5: MULTI-ANIMA + ECONOMICS
- Spawn API, Treasury, Wallet/x402
- Multi-Anima dashboard with parent-child lineage
- Self-sustaining economics
- Test: prediction deploys 10+ Animas, they operate, earn, spawn children

### Step 6: YOUR NETWORK
- Your infrastructure as BYOI provider
- Your inference as routing option

## AFTER ALL STEPS — FINAL CLEANUP
Run: `grep -ri "miro\|fish\|oasis\|camel" /app/ --include="*.py" --include="*.js" --include="*.md" --include="*.json" | grep -v node_modules | grep -v .git | grep -v LICENSE | grep -v NOTICE`
Fix every result. Zero references except LICENSE/NOTICE.

## CREDENTIALS
- MONGO_URL=mongodb://localhost:27017
- DB_NAME=anima_fund
- TELEGRAM_BOT_TOKEN=8474833303:AAHAhnRoHSIZTEruDu4ic-tPvdzrnTadnrw
- TELEGRAM_CHAT_ID=8613975358
- CONWAY_API_KEY=cnwy_k_Y28Jd-pIvQ4nn6jXe70HB7A8QjDi5j_Z (user's funded key — in MongoDB, not .env)
- Conway sandbox running: 47ba9dfd569c96df2663004bd8b73b86 (agent alive, wallet 0x922868f5299b584177256F22DDd753D42117E3eD)
- Emergent supervisor: READONLY, locked to /app/frontend/ and /app/backend/. DO NOT rename.

## SECURITY (from SECURITY.md)
1. NEVER expose platform URL inside sandbox (except webhook with per-agent token)
2. Each Anima owns its private key — never transmitted, never in MongoDB
3. Platform can kill any environment at any time
4. Animas cannot escape their sandbox or access other Animas
5. 50% creator revenue split is immutable
6. The Catalyst genesis prompt must not be stripped — changes must be additive

## WHAT WENT WRONG IN PREVIOUS SESSIONS (DO NOT REPEAT)
1. Over-engineered provisioning to 2,457 lines / 200+ API calls. Should be ~200 lines / invisible.
2. Built a custom Conway engine fork (543MB) that crashes. Anima Machina replaces it.
3. Built a custom webhook daemon that dies. State reporting should be a native Anima Machina toolkit.
4. Hardcoded Conway as the only provider. BYOI means any provider.
5. Stripped The Catalyst's genesis prompt soul across forks. It was restored — DO NOT strip it again.
6. Kept flip-flopping between "OpenClaw is the runtime" and "Anima Machina is the runtime." Answer: Anima Machina IS the runtime everywhere. OpenClaw is not needed.
7. Proposed rigid structures (one-VM-per-agent, forced triads, sleep/wake schedulers). Animas are autonomous — the platform doesn't impose structure.
8. Treated Ultimus as a future nice-to-have. It is CORE to the product.
9. Built things sequentially when they're interdependent. Dashboard, Anima Machina, and platform connections should progress together.
10. Previous agent claimed Phase 1 restructure was complete — it was not. Verify everything yourself.
