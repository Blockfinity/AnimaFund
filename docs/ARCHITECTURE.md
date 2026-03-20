# Anima Platform — Final Architecture (v3)
# This supersedes all previous architecture documents.
# Any AI agent forking this chat reads THIS FIRST.

## THE PRODUCT

Anima is a platform to launch, monitor, and manage fully autonomous AI agents.
Each agent runs in its own sandboxed VM with full autonomy to achieve the goals
assigned to it — using whatever tools, skills, and strategies it needs.

The platform is the CONTROL PLANE. OpenClaw is the TOOL LAYER. The genesis prompt
is the MISSION. The simulation layer generates missions from predictions.

## THREE LAYERS

### Layer 1: Platform (we build this)
The control plane. Users and simulations interact with the platform. It:
- Provisions VMs on the user's chosen infrastructure (BYOI)
- Configures inference routing (which LLM providers, models, API keys, cost tiers)
- Pushes genesis prompts (goals, identity, rules) into each agent's VM
- Monitors all agents (wallets, state, logs, economics, goal progress)
- Serves the spawn API so agents can request child VMs THROUGH the platform
- Tracks every agent's wallet, parent lineage, and economics

The platform decides WHERE agents run and WHAT inference they use.
Agents do NOT freelance on infrastructure or inference — they use what's configured.

### Layer 2: OpenClaw (installed in each VM)
The capability layer. Gives each agent:
- Browser automation (navigate, click, extract, fill forms)
- Shell execution (run any command)
- Persistent memory (semantic recall)
- Self-modification (SOUL.md evolution, skill creation)
- ClawHub skills (discover and install any skill)
- MCP protocol support (connect to any MCP server)
- Telegram/Discord/WhatsApp channels

OpenClaw does NOT decide goals, infrastructure, or inference routing.
It provides capabilities. The genesis prompt directs their use.

### Layer 3: Agent (directed by genesis prompt)
Each agent executes the goals in its genesis prompt using OpenClaw's capabilities.
The genesis prompt contains:
- Identity (who you are, personality, SOUL.md seed)
- Goals (what to achieve — from user or from simulation)
- Inference config (what models to use, API keys, cost tiers — from platform)
- Platform spawn API (how to request child VMs — through the platform)
- Telegram config (how to report)
- Creator wallet (where to send revenue split)
- Skills to prioritize
- Rules and constraints

The agent CAN spin up child agents by calling the platform's spawn API.
The PLATFORM decides where that child VM runs (based on BYOI config).
The AGENT writes the child's genesis prompt (within its mission bounds).

## BYOI (Bring Your Own Infrastructure)
The platform — NOT the agent — provisions VMs. Available providers:
- Conway Cloud (current)
- Fly.io (current, trial expired)
- Docker (local development)
- Your network (future — agents deploy on YOUR infrastructure)
- Any VPS with API (DigitalOcean, Hetzner, AWS — future)

User selects provider + tier in the platform UI. The platform handles the API.
When an agent requests a child VM via the spawn API, the platform uses the
same BYOI config to provision it.

## INFERENCE ROUTING
The platform — NOT the agent — decides inference configuration:
- Which providers are available (OpenAI, Anthropic, Gemini, local, your network)
- Which models at each cost tier (critical/budget/normal/premium)
- API keys for each provider
- Cost limits per agent

This config is pushed to the agent via the genesis prompt or a config file.
The agent selects models within these bounds based on task importance and balance.

Future: your network provides inference nodes. The platform routes agents to
your network's inference API. Agents pay via x402. Your network earns.

## SIMULATION LAYER (MiroFish/OASIS Fork)
Generates genesis prompts from predictions:
1. User describes a goal ("expand to 3,000 nodes")
2. Simulation runs thousands of agent personas
3. Produces: strategy, roles, costs, expected revenue, confidence scores
4. Bridge converts strategy into N genesis prompts (one per agent)
5. Cost calculator shows user: seed cost, break-even, projected value
6. User clicks Launch → platform provisions VMs, pushes genesis prompts, starts agents
7. Feedback: real results feed back into next simulation

The simulation layer sits ON TOP of the platform. It uses the platform's
provisioning + spawn APIs. It does not replace them.

## YOUR NETWORK INTEGRATION
Two components:
1. BYOI provider: your network as an infrastructure option (agents run on your nodes)
2. Inference provider: your network serves LLM inference (agents pay via x402)

Agents can also DEPLOY new nodes on your network (using OpenClaw's shell/browser
capabilities + your network's SDK). This is directed by the genesis prompt —
"deploy 10 nodes on [network]" is a goal, not a platform feature.

## WHAT EXISTS IN THE CODEBASE (March 2026)

### Keep:
- Frontend dashboard (14 pages, 3-screen flow, SSE pipeline) — ~6,500 lines
- Agent CRUD + MongoDB state management — agents.py, agent_state.py
- BYOI provider abstraction — sandbox_provider.py (needs slimming)
- Genesis prompt (The Catalyst soul — restored) — genesis-prompt.md
- Constitution — constitution.md
- 96 custom skills — automaton/skills/
- Telegram integration — telegram.py
- Security model — SECURITY.md
- Webhook receiver — webhook.py
- SSE hooks — useSSE.js

### Delete:
- automaton/dist, native, node_modules, src, packages (543MB Conway fork)
- engine_bridge.py (1,108 lines dead code)
- payment_tracker.py (142 lines dead code)
- webhook_daemon_template.py (72 lines — daemon that dies)
- active_agent.txt (legacy file state)

### Rewrite:
- agent_setup.py (2,457 lines → ~200 lines)
  Current: 200+ API calls, installs Node.js, Conway Terminal, pushes 10MB bundle
  Target: create VM → install OpenClaw → push config → start
- sandbox_poller.py (321 lines → ~100 lines or eliminate)
  Current: reads JSON files that don't exist
  Target: agent reports state natively, or read from OpenClaw's state on-demand
- genesis.py + live.py + infrastructure.py → monitor.py (~200 lines)
  Current: multiple files with overlapping responsibility
  Target: one file that reads agent state from OpenClaw's native output

## PROVISIONING FLOW (Target)

Step 1: Create VM via BYOI provider (one API call)
Step 2: Install OpenClaw (one exec: curl -fsSL https://openclaw.ai/install.sh | bash)
Step 3: Configure OpenClaw (push genesis prompt + inference config + skills)
Step 4: Start agent (one exec: openclaw agent or openclaw gateway)

4 steps. 4 API calls. No file corruption. No binary transfer. No 200-call provisioning.

The 96 custom skills get pushed via OpenClaw's native skill loading mechanism.
The wallet + x402 is an OpenClaw skill the agent installs.
Inference routing config is part of the genesis prompt or OpenClaw config.

## DASHBOARD DATA FLOW (Target)

Agent (in VM) → reports state to platform webhook (built into OpenClaw config)
Platform webhook → updates in-memory cache
SSE stream → pushes updates to frontend
Dashboard pages → read from cache

For on-demand data: platform exec's into sandbox, reads OpenClaw's state.
No custom daemon. No custom JSON files. No polling files that don't exist.

## MULTI-AGENT WALLET VIEW

Every agent creates its own wallet inside its VM (OpenClaw + wallet skill).
The agent reports its wallet address to the platform via the webhook.
The platform stores wallet addresses in MongoDB agent records.
The dashboard shows ALL agent wallets — parent and children.
Each wallet has a QR code for funding.

## CONCRETE TASK LIST

### Immediate (get one working agent):
1. Delete bloat (automaton/dist, native, node_modules, src, dead code files)
2. Rewrite provisioning (~200 lines)
3. Connect dashboard to OpenClaw's native state output
4. Test: one agent boots, wallet shows, logs stream, Telegram reports

### Next (multi-agent + directed autonomy):
5. Spawn API (agents request child VMs through platform)
6. Multi-agent wallet view on dashboard
7. Inference routing config (pushed to agents via genesis prompt)
8. User can set BYOI provider + inference config per agent

### Future (simulation + network):
9. Fork MiroFish/OASIS
10. Build simulation → genesis prompt bridge
11. Your network as BYOI provider
12. Your network as inference provider

## CRITICAL RULES (unchanged from SECURITY.md)
1. NEVER expose platform URL inside sandbox (except webhook endpoint with token)
2. NEVER transfer large binaries via base64/exec
3. Each agent owns its private key — never transmitted, never in MongoDB
4. 50% creator split is immutable
5. Skills are YOUR IP
6. The genesis prompt is sacred — changes must be additive
