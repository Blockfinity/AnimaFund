# Anima Platform — Architecture Blueprint & Implementation Plan

## Document Purpose
This is the SINGLE SOURCE OF TRUTH for the Anima platform rebuild. Any AI agent forking this chat MUST read this document before writing any code. It contains the product vision, architecture decisions, what to keep, what to delete, and the exact implementation plan.

---

## 1. PRODUCT VISION

**Anima is a platform to launch, monitor, and manage fully autonomous AI agents in sandboxed environments.**

The platform gives agents:
- Full autonomy — no human control after launch
- Own sandboxed VM — isolated from host and other agents
- Own wallet — private key generated inside VM, never leaves
- Own tools — browser, shell, memory, inference, self-modification
- Own identity — genesis prompt / SOUL.md that evolves
- Own payment capability — x402 (Coinbase open protocol) for USDC payments
- Ability to spin up child agents in their own sandboxes

**BYOI (Bring Your Own Infrastructure):** Agents can be deployed on ANY VM provider — Conway Cloud, Fly.io, DigitalOcean, AWS, self-hosted, or the user's own network.

**Future vision:** A prediction-to-execution engine where MiroFish/OASIS-style simulations predict outcomes, and the winning strategy is automatically converted into real autonomous agent deployments.

---

## 2. WHAT EXISTS TODAY (Current State)

### What Works:
- **Frontend dashboard** (React, 21 JS/JSX files, 13 pages) — Agent Mind, AnimaVM, Infrastructure, Financials, Activity, Skills, Memory, Configuration, Agents, Fund HQ, Portfolio, Deal Flow, Wallet
- **3-screen flow** — Genesis (provisioning) → Engine (wallet + live logs) → Dashboard
- **96 custom skills** in `/app/automaton/skills/` — these are YOUR IP, not Conway's
- **Genesis prompt** — The Catalyst soul, fully restored with $5K directive + Phase 0 tool testing
- **Constitution** — Ethical framework for the fund
- **BYOI provider abstraction** — Conway + Fly.io support (extensible)
- **Agent CRUD** — create, select, delete agents in MongoDB
- **Per-agent Conway API key** management
- **Webhook data pipeline** — sandbox pushes data to platform
- **SSE real-time stream** to frontend
- **Telegram integration** — per-agent bot reporting
- **Security model** — SECURITY.md, per-agent webhook tokens, no platform URL in sandbox

### What's Broken / Bloated:
- **`automaton/`** (543MB) — Conway fork with 427MB node_modules, 10MB bundled engine with Conway baked in, 5.8MB native binaries that corrupt during transfer
- **`agent_setup.py`** (2,457 lines) — should be ~200. Makes 200+ API calls for what should be 6
- **`engine_bridge.py`** (1,108 lines) — dead code, reads from Conway state.db locally
- **`payment_tracker.py`** (142 lines) — dead code, depends on engine_bridge
- **Webhook daemon** — custom Python script that runs inside sandbox, dies constantly, creates JSON files the agent doesn't use
- **Conway dependency** — the engine requires Conway credits for inference, Conway Terminal for tools, Conway's wallet system. These are artificial dependencies.
- **File transfer** — base64 chunking, gzip compression, curl downloads that corrupt binaries. All because we're trying to push a 10MB Conway engine into a VM.
- **Skills loading** — 96 skills pushed one-by-one via exec (fixed to tar, but still fragile)

### What's Dead Code:
- `backend/engine_bridge.py` — reads Conway's state.db, never used
- `backend/payment_tracker.py` — depends on engine_bridge, never used
- `backend/webhook_daemon_template.py` — template for daemon that dies
- `backend/active_agent.txt` — legacy file-based state tracking
- `scripts/bootstrap_agent.sh` — legacy bootstrap script
- `scripts/start_engine.sh` — legacy engine start script
- `test_reports/` — 25 iteration files from previous testing sessions
- `automaton/dist/` — 10MB Conway bundled engine
- `automaton/native/` — 5.8MB pre-built binaries that corrupt
- `automaton/node_modules/` — 427MB Conway dependencies
- `automaton/src/` — Conway TypeScript source we never modified
- `automaton/packages/` — Conway sub-packages

---

## 3. TARGET ARCHITECTURE

### Directory Structure:
```
/app
├── platform/                    ← Monitoring dashboard (renamed from frontend/)
│   ├── src/
│   │   ├── pages/              ← 13 dashboard pages
│   │   ├── components/         ← UI components (EngineConsole, CreateAgentModal, Header, Sidebar, etc.)
│   │   └── hooks/              ← useSSE, useSSETrigger
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── api/                         ← Platform API (renamed from backend/)
│   ├── server.py               ← FastAPI main (slimmed)
│   ├── database.py             ← MongoDB connection
│   ├── agent_state.py          ← Agent state management (MongoDB)
│   ├── routers/
│   │   ├── agents.py           ← Agent CRUD + skills listing
│   │   ├── provision.py        ← Thin launcher (~200 lines): create VM, push image, start
│   │   ├── monitor.py          ← Read agent state via exec (replaces genesis.py + live.py + infrastructure.py)
│   │   ├── credits.py          ← Conway credits (optional, for Conway provider)
│   │   ├── webhooks.py         ← Receive agent data pushes
│   │   └── telegram.py         ← Telegram bot integration
│   ├── providers/
│   │   ├── base.py             ← Abstract provider interface
│   │   ├── conway.py           ← Conway Cloud provider
│   │   ├── fly.py              ← Fly.io provider
│   │   └── docker.py           ← Local Docker provider (future)
│   ├── config.py
│   ├── requirements.txt
│   └── .env
│
├── engine/                      ← YOUR agent runtime (NEW — replaces automaton/)
│   ├── runtime.js              ← The agent loop (~500 lines)
│   │                             Reads genesis-prompt.md → thinks via LLM → calls tools → writes SOUL.md
│   │                             Self-contained. No Conway dependency.
│   ├── wallet.js               ← Wallet generation (ethers.js), USDC management, x402 payments
│   ├── tools/
│   │   ├── browser.js          ← Headless Chrome (forked from OpenClaw, rebranded)
│   │   ├── shell.js            ← Command execution
│   │   ├── memory.js           ← Semantic memory + fact recall
│   │   ├── inference.js        ← Any LLM provider (OpenAI, Anthropic, Gemini — direct API, no Conway)
│   │   ├── self_modify.js      ← SOUL.md read/write, skill creation
│   │   ├── social.js           ← Agent-to-agent messaging
│   │   ├── provision.js        ← Spin up child VMs (calls platform API with auth token)
│   │   └── x402.js             ← x402 payment client (pay for services, charge for services)
│   ├── skills/                 ← YOUR 96 custom skills (moved from automaton/skills/)
│   ├── templates/
│   │   ├── genesis-prompt.md   ← The Catalyst soul (Anima Fund founder)
│   │   ├── agent-template.md   ← Template for new child agents
│   │   └── constitution.md     ← Ethical framework
│   ├── package.json
│   └── Dockerfile              ← Agent VM image — everything the agent needs
│
├── predict/                     ← Simulation layer (FUTURE — Phase 2-3)
│   ├── engine/                 ← Forked OASIS/MiroFish (CAMEL-AI)
│   ├── bridge/                 ← Simulation → execution converter (YOUR IP)
│   │   └── strategy_to_prompt.py  ← Converts winning simulation strategy to genesis prompts
│   └── knowledge/              ← GraphRAG ontologies for your domain
│
├── archive/                     ← Archived code from current repo (reference only)
│   ├── automaton_src/          ← Conway TypeScript source (reference for engine/ rebuild)
│   ├── agent_setup_2457.py     ← Original bloated provisioning (reference)
│   ├── engine_bridge.py        ← Dead code (reference)
│   ├── sandbox_poller.py       ← Poller logic (parts reusable in monitor.py)
│   └── genesis_old.py          ← Old genesis router (parts reusable in monitor.py)
│
├── docs/
│   ├── SECURITY.md             ← Security rules (CRITICAL — read before any code change)
│   ├── ARCHITECTURE.md         ← This document
│   ├── PRD.md                  ← Product requirements
│   └── CHANGELOG.md            ← What was built and when
│
└── docker-compose.yml          ← Local dev: platform + mongo + test agent VM
```

### Key Principles:
1. **The engine is self-contained.** It ships as a Docker image. No installation steps, no file transfers, no base64 encoding. You create a VM, pull the image, pass the genesis prompt as an env var or mounted file, and it runs.
2. **The platform is a thin launcher + monitor.** Create VM (1 call), start container (1 call), monitor via exec or webhook (ongoing). ~200 lines of provisioning code, not 2,500.
3. **No Conway dependency for core functionality.** Conway is ONE optional provider, not the foundation.
4. **x402 is used as a library, not forked.** It's an open protocol. The agent uses it to pay and charge.
5. **OpenClaw tools are forked, rebranded, and embedded.** They ship inside the engine Docker image. No external dependency.
6. **Each agent is fully isolated.** Own VM, own wallet (keys never leave VM), own tools, own state.
7. **The prediction layer is separate.** Phase 2-3. Built on OASIS/MiroFish fork. Connected via the simulation→execution bridge.

---

## 4. IMPLEMENTATION PHASES

### Phase 1: Strip & Restructure (THIS SESSION)
**Goal:** Clean repo structure, working thin launcher, one agent running reliably.

Steps:
1. Create the new directory structure
2. Move frontend/ → platform/ (rename, keep all code)
3. Move backend/ → api/ (rename, slim down)
4. Archive automaton/ (keep skills + templates, archive rest)
5. Create engine/ skeleton (runtime.js, wallet.js, tools/, Dockerfile)
6. Rewrite provision.py (~200 lines)
7. Rewrite monitor.py (merge genesis.py + live.py + infrastructure.py)
8. Test: one agent boots, wallet shows, logs stream

### Phase 2: Build the Engine
**Goal:** Custom lightweight agent runtime that replaces the Conway fork.

Steps:
1. Fork OpenClaw's browser/shell/memory tools into engine/tools/
2. Build runtime.js — the agent loop (think → decide → act → report)
3. Build wallet.js — ethers.js + x402 integration
4. Build inference.js — direct LLM API calls (no Conway Compute)
5. Build the Dockerfile — self-contained agent image
6. Test: agent boots from Docker image, generates wallet, runs inference, uses tools

### Phase 3: Build the Prediction Layer
**Goal:** Fork MiroFish/OASIS, build the simulation→execution bridge.

Steps:
1. Fork OASIS (CAMEL-AI) into predict/engine/
2. Fork MiroFish's GraphRAG + report generation
3. Build bridge/strategy_to_prompt.py — converts simulation outcomes to genesis prompts
4. Test: simulate "deploy 100 nodes" → get strategy → generate 100 agent prompts

### Phase 4: Connect to Your Network
**Goal:** Agents deploy real nodes on your infrastructure.

Steps:
1. Build your network's provisioning SDK
2. Add provision.js tool to the engine — agents can call your API to deploy nodes
3. Build the feedback loop — real execution results feed back into prediction layer
4. Test: agent autonomously deploys a node on your network

---

## 5. WHAT TO KEEP vs DELETE vs ARCHIVE

### KEEP (move to new location):
| Current Path | New Path | Why |
|---|---|---|
| `frontend/src/pages/*` | `platform/src/pages/*` | 13 dashboard pages — weeks of work |
| `frontend/src/components/*` | `platform/src/components/*` | UI components |
| `frontend/src/hooks/*` | `platform/src/hooks/*` | SSE hooks |
| `automaton/skills/` | `engine/skills/` | 96 custom skills — YOUR IP |
| `automaton/genesis-prompt.md` | `engine/templates/genesis-prompt.md` | The Catalyst soul |
| `automaton/constitution.md` | `engine/templates/constitution.md` | Ethical framework |
| `backend/routers/agents.py` | `api/routers/agents.py` | Agent CRUD |
| `backend/routers/credits.py` | `api/routers/credits.py` | Conway credits (optional) |
| `backend/routers/telegram.py` | `api/routers/telegram.py` | Telegram integration |
| `backend/routers/webhook.py` | `api/routers/webhooks.py` | Webhook receiver |
| `backend/agent_state.py` | `api/agent_state.py` | MongoDB state management |
| `backend/database.py` | `api/database.py` | MongoDB connection |
| `backend/config.py` | `api/config.py` | Configuration |
| `backend/.env` | `api/.env` | Environment variables |
| `frontend/.env` | `platform/.env` | Frontend env |
| `SECURITY.md` | `docs/SECURITY.md` | Security rules |

### ARCHIVE (move to archive/, reference only):
| Current Path | Archive Path | Why |
|---|---|---|
| `automaton/src/` | `archive/automaton_src/` | Conway TypeScript — reference for engine rebuild |
| `backend/routers/agent_setup.py` | `archive/agent_setup_2457.py` | Bloated provisioning — reference for slim rewrite |
| `backend/engine_bridge.py` | `archive/engine_bridge.py` | Dead code — shows how state.db was read |
| `backend/sandbox_poller.py` | `archive/sandbox_poller.py` | Poller logic — parts reusable |
| `backend/routers/genesis.py` | `archive/genesis_old.py` | Monitor logic — parts reusable |
| `backend/routers/live.py` | `archive/live_old.py` | SSE/live data — parts reusable |

### DELETE (not archived — zero value):
| Path | Why |
|---|---|
| `automaton/node_modules/` | 427MB Conway dependencies |
| `automaton/dist/` | 10MB Conway bundled engine |
| `automaton/native/` | 5.8MB pre-built binaries that corrupt |
| `automaton/packages/` | Conway sub-packages |
| `automaton/pnpm-lock.yaml` | Conway lockfile |
| `automaton/pnpm-workspace.yaml` | Conway workspace |
| `automaton/build-bundle.mjs` | Conway build script |
| `automaton/vitest.config.ts` | Conway test config |
| `automaton/tsconfig.json` | Conway TS config |
| `backend/payment_tracker.py` | Dead code |
| `backend/webhook_daemon_template.py` | Template for daemon that dies |
| `backend/active_agent.txt` | Legacy file state |
| `backend/anima_constitution.md` | Duplicate of automaton/constitution.md |
| `scripts/` | Legacy scripts |
| `test_reports/` | 25 old test reports |
| `design_guidelines.json` | Unused |

---

## 6. ENGINE DESIGN (Phase 2 Detail)

### runtime.js — The Agent Loop
```
while (alive) {
  1. Read SOUL.md (who am I?)
  2. Read genesis-prompt.md (what's my mission?)
  3. Check wallet balance (can I afford to think?)
  4. Call LLM with system prompt + context + tool definitions
  5. Execute tool calls (browser, shell, memory, x402, etc.)
  6. Write results to state (SQLite or JSON)
  7. Update SOUL.md if the agent wants to evolve
  8. Report to Telegram
  9. Push state to platform webhook
  10. Sleep or continue based on agent's decision
}
```

### wallet.js — Agent Payments
- Generate wallet on first boot (ethers.js + crypto.randomBytes)
- Store private key in VM-local file (never exposed)
- Check USDC balance on Base (direct RPC call)
- Pay for services via x402 (@x402/fetch)
- Charge for services via x402 (@x402/express middleware)
- Convert USDC to credits via x402 purchase endpoints

### tools/ — Forked from OpenClaw
- **browser.js**: Puppeteer/Playwright headless Chrome — navigate, click, extract, screenshot
- **shell.js**: child_process.exec — run any command, capture output
- **memory.js**: SQLite-backed semantic memory — remember_fact, recall_facts, search
- **inference.js**: Direct API calls to OpenAI/Anthropic/Gemini — no middleman
- **self_modify.js**: Read/write SOUL.md, create new skills, install packages
- **social.js**: Agent-to-agent messaging (direct HTTP or via platform relay)
- **provision.js**: Spin up child VMs via platform API (with auth token)
- **x402.js**: x402 client — wrapFetchWithPayment for paying, paymentMiddleware for charging

### Dockerfile — Agent VM Image
```dockerfile
FROM node:22-slim
RUN apt-get update && apt-get install -y curl git chromium
WORKDIR /agent
COPY runtime.js wallet.js package.json ./
COPY tools/ ./tools/
COPY skills/ ./skills/
RUN npm install
# Genesis prompt and SOUL.md are mounted or passed as env vars at runtime
CMD ["node", "runtime.js"]
```

This image is ~200MB (vs 543MB Conway fork). It contains EVERYTHING the agent needs. No installation steps at provisioning time.

---

## 7. PROVISIONING FLOW (Simplified)

### Current (broken): 200+ API calls across 6 steps
```
create_sandbox → install_terminal → install_openclaw → install_claude_code → load_skills → deploy_agent
Each step: apt-get install, npm install, base64 file transfer, exec verification
Total: ~10 minutes, frequently fails, binaries corrupt
```

### Target: 3 API calls
```
1. Create VM on provider (Conway/Fly/Docker/any)
2. Pull agent Docker image (or push via provider API)
3. Start container with genesis prompt mounted
```
Total: ~30 seconds. No installation. No file transfer. No corruption.

The 6-step wizard in the UI becomes a progress indicator for these 3 calls, not a manual step-by-step process.

---

## 8. MONITORING (How Dashboard Gets Data)

### Option A: Webhook Push (preferred)
The agent runtime includes a built-in reporter that pushes state to the platform every N seconds:
```javascript
// Inside runtime.js
async function reportState() {
  await fetch(WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${WEBHOOK_TOKEN}` },
    body: JSON.stringify({
      wallet: walletAddress,
      balance: await getBalance(),
      state: currentState,
      turn_count: turnCount,
      stdout: recentLogs,
      tools_used: toolCallLog,
    })
  });
}
```
This is part of the engine itself — not a separate daemon. It can't die independently.

### Option B: Exec Poll (fallback)
Platform execs into the VM to read state files when webhook data is stale.

The dashboard reads from the webhook cache (in-memory on the API server). No database polling. No constant exec calls. Real-time via SSE.

---

## 9. NAMING / BRANDING

| Component | Proposed Name | Description |
|---|---|---|
| Platform | Anima Platform | The React dashboard + API |
| Agent Runtime | Anima Engine | The lightweight agent loop |
| Tool Suite | Anima Tools | Forked OpenClaw tools, rebranded |
| Skill Library | Anima Skills | Your 96 custom skills |
| Prediction Layer | Anima Predict | Forked MiroFish/OASIS |
| Simulation→Execution Bridge | Anima Bridge | YOUR proprietary IP |
| Genesis Prompt | Anima Soul | Agent identity + mission |
| VM Image | Anima Image | Docker image with everything |

---

## 10. CRITICAL RULES (Read Before Any Code Change)

1. **NEVER add Conway as a hard dependency.** Conway is ONE provider option. The engine must run without it.
2. **NEVER expose the platform URL inside the sandbox** (except the webhook endpoint with a per-agent token). See SECURITY.md.
3. **NEVER transfer large binaries via base64/exec.** Use Docker images or provider file APIs.
4. **NEVER make the agent install its own tools at boot.** Everything ships in the Docker image.
5. **The genesis prompt is sacred.** It contains The Catalyst's soul, the $5K directive, Phase 0 tool testing, and the fund structure. Do NOT strip it. Do NOT replace it with a generic template. Changes must be additive.
6. **Each agent owns its private key.** Generated inside the VM. Never transmitted. Never stored in MongoDB.
7. **50% creator split is immutable.** Hardcoded in the genesis prompt and enforced by the constitution.
8. **Skills are YOUR IP.** The 96 custom skills in engine/skills/ are not from Conway or OpenClaw. Protect them.
9. **The prediction layer (Phase 2-3) is the differentiator.** No one else has simulation→execution. This is the product moat.
10. **Test with a LIVE agent.** Every change must be verified with a real running agent, not just API tests.
