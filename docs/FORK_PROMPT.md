# FORK PROMPT — COMPLETE RESET

## STOP. READ THIS ENTIRE DOCUMENT. DO NOT SKIP ANYTHING.

Multiple previous agents have deviated from the product requirements, built things that weren't asked for, claimed work was done that wasn't, and wasted over $1,000 in credits. This prompt exists because of that history. Follow it EXACTLY.

## THE SITUATION

After 10+ sessions and $1,000+ in Emergent credits:
- The CORE PRODUCT (Ultimus — the prediction engine) has ZERO code. Not started.
- The dashboard shows data from ONE agent that ran for a few turns before Conway credits ran out ($0.09 remaining)
- The CAMEL fork is NOT rebranded (18+ "camel" references in our code, thousands in the CAMEL internals)
- x402 payments are a STUB (just a message saying "handled in sandbox")
- BYOI is Conway-only with hardcoded if/else
- Spawn records in MongoDB but provisions NOTHING
- No multi-agent dashboard, no agent selector, no aggregate views
- No Ultimus screens (no goal input, no simulation, no Dimensions, no cost calculator, no execute)
- No JWT auth on any endpoint
- Ultima X is files in a directory, not integrated
- Dashboard pages show inconsistent, mock, stub, hardcoded, or disconnected data
- AnimaVM returns nothing
- The agent focused on Conway sandbox fixes instead of building the product

## WHAT THE PRODUCT IS (do not deviate from this)

### Anima Platform
A platform to launch, monitor, and manage fully autonomous AI agents (Animas) in sandboxed environments. Users define goals either manually or through Ultimus. Animas operate autonomously to achieve those goals.

### Three Systems:

**1. Anima Machina** (CAMEL fork, Apache-2.0, MUST be fully rebranded)
- Creates agents. Runs them. Gives them tools, memory, personas, inference routing.
- Runs on the platform server for Ultimus simulations AND inside sandboxed environments as the agent runtime.
- 50+ native toolkits. Custom additions: WalletToolkit, SpawnToolkit, StateReportingToolkit.
- ZERO "camel" references in ANY user-facing code, UI, logs, API responses.

**2. Ultimus** (THIS IS THE CORE PRODUCT — it has ZERO code right now)
- Prediction/simulation engine built on Anima Machina.
- User describes a goal -> Ultimus simulates with thousands of personas -> produces a prediction.
- Each persona has: personality, memory, behavioral logic, social relationships, actions.
- Prediction includes per-agent specs: auto-generated genesis prompt, skills, budget, actions, success criteria.
- Three sub-processes: Predictor (simulates), Calculator (costs/feasibility/resources), Executor (deploys).
- Four seed data modes: Quick (goal only), Deep (auto-research), Expert (user uploads), Iterative (hybrid).
- Dimensions (God's-eye view): observe personas during simulation, observe live Animas after execution, chat with any agent, inject variables.
- When user clicks Execute: personas become real Animas. Platform provisions environments. Animas operate autonomously to make the prediction happen.
- Every prediction must be self-sustaining. Seed capital starts it. Animas earn to cover costs.
- Predictions are non-linear. Thousands of paths explored simultaneously. 100 predicted steps might resolve in 1 action.
- Dashboard SCREENS (not a separate app): goal input, simulation progress, Dimensions, cost review, execute button.
- NO MiroFish code. Built from scratch on Anima Machina. Study MiroFish README-EN for workflow concepts ONLY (https://github.com/666ghj/MiroFish/blob/main/README-EN.md).

**3. Platform** (thin control plane)
- Provisions sandboxed environments via BYOI (ANY provider API — user provides endpoint + key).
- Monitors ALL Animas (wallets, state, logs, economics, goal progress).
- Spawn via webhook (Animas request environments through WEBHOOK_URL).
- Dimensions live mode.
- Kill switch.
- Dashboard: multi-agent overview + drill-down + Ultimus screens.

## WHAT TO DO — EXACT ORDER, NO DEVIATIONS

### Step 1: AUDIT (before writing any code)
Run every command below and post the COMPLETE raw output. Do not summarize.

```bash
echo "=== 1. Ultimus exists? ==="
find /app -name "ultimus*" -o -name "predictor*" -o -name "calculator*" -o -name "dimensions*" | grep -v node_modules | grep -v __pycache__

echo "=== 2. Camel references in our code ==="
grep -ri "camel" /app/backend/ --include="*.py" | grep -v __pycache__ | grep -v archive
grep -ri "camel" /app/frontend/ --include="*.js"
grep -ri "camel" /app/engine/ --include="*.py" 2>/dev/null

echo "=== 3. x402 implementation ==="
grep -rn "x402\|send_payment\|sweep_public" /app/backend/ /app/engine/ --include="*.py" | grep -v __pycache__ | grep -v archive

echo "=== 4. BYOI providers ==="
find /app/backend/providers/ -name "*.py" 2>/dev/null
grep -n "conway\|if.*provider" /app/backend/routers/provision.py 2>/dev/null | head -20

echo "=== 5. Spawn implementation ==="
cat /app/backend/routers/spawn.py 2>/dev/null | head -50

echo "=== 6. Dashboard pages and what they fetch ==="
for page in /app/frontend/src/pages/*.js; do
    echo "--- $(basename $page) ---"
    grep "fetch\|api/" $page | head -5
done

echo "=== 7. Endpoints that return real data ==="
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
for ep in health agents monitor/agent-state/anima-fund monitor/financials monitor/activity monitor/infrastructure spawn/list; do
    echo "--- /api/$ep ---"
    curl -s --max-time 3 "$API_URL/api/$ep" 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print('EMPTY' if not any(v for v in d.values() if v and v!=0 and v!=[] and v!={} and v!=False) else 'HAS_DATA')" 2>/dev/null || echo "FAILED"
done

echo "=== 8. Miro/fish/oasis references ==="
grep -ri "miro\|fish\|oasis" /app/ --include="*.py" --include="*.js" --include="*.md" | grep -v node_modules | grep -v .git | grep -v LICENSE | grep -v NOTICE | grep -v archive

echo "=== 9. File structure ==="
find /app -maxdepth 2 -type d | grep -v node_modules | grep -v __pycache__ | grep -v .git | sort

echo "=== 10. What's in the Conway sandbox ==="
CONWAY_KEY="cnwy_k_Y28Jd-pIvQ4nn6jXe70HB7A8QjDi5j_Z"
SID="47ba9dfd569c96df2663004bd8b73b86"
curl -s "https://api.conway.tech/v1/credits/balance" -H "Authorization: Bearer $CONWAY_KEY" 2>/dev/null
```

### Step 2: REBRAND (complete this fully)
- Every "camel" reference in backend/, frontend/, engine/ code -> "anima_machina"
- Module imports, config files, env vars, log prefixes, API responses
- Keep LICENSE + NOTICE in anima-machina/ directory
- Verify: `grep -ri "camel" /app/backend/ /app/frontend/ /app/engine/ --include="*.py" --include="*.js" | grep -v node_modules | grep -v archive | wc -l` returns 0

### Step 3: FIX THE DASHBOARD
- Remove ALL mock/stub/hardcoded/dummy data from every page
- Every page shows REAL data from the per-agent state store or shows "No data — deploy an Anima to see activity"
- Core wallet displayed with QR code on wallet screen and agent mind sidebar
- Multi-agent foundation: agent selector dropdown, show all registered Animas
- AnimaVM must show real sandbox data or "No sandbox connected"
- Do NOT fill pages with fake data to make them look populated

### Step 4: BUILD ULTIMUS (THE CORE PRODUCT)
This is what you spend the MAJORITY of your time on. Everything else is prerequisite.

```
/app/ultimus/
├── predictor.py      — Simulation runner using Anima Machina multi-agent societies
├── calculator.py     — Infrastructure needs, costs, feasibility, resource planning
├── executor.py       — Convert persona specs to real Anima deployments via platform
├── knowledge.py      — GraphRAG integration for seed data
├── personas.py       — Persona generation from knowledge graph
├── dimensions.py     — God's-eye view API (simulation + live modes)
├── api.py            — REST endpoints for the frontend
└── config.py         — Ultimus configuration
```

Frontend screens (add to existing dashboard):
- **Goal Input**: User types what they want ("Make me $1000 in memecoins")
- **Simulation Progress**: Watch personas interact in real-time
- **Dimensions**: Observe any persona, chat with it, inject variables, rerun
- **Cost Review**: Seed cost, break-even, projected value, resource breakdown
- **Execute**: One button. Platform provisions environments, deploys Animas.
- **Live Monitoring**: Dimensions switches to live mode — observe real Animas

Test scenario: "Make me $1000 in memecoins"
- Ultimus simulates hundreds of strategies with thousands of personas
- Non-linear: create tokens, trade, amplify on social media, build communities — ALL paths explored simultaneously
- Calculator determines: N Animas needed, M environments, $X seed cost
- User reviews in Dimensions, adjusts, clicks Execute
- Animas deploy and operate autonomously to make the prediction happen
- Results feed back to Ultimus

### Step 5: SPAWN VIA WEBHOOK
- Animas request child environments through the existing WEBHOOK_URL
- Payload: `{"type": "spawn_request", "genesis_prompt": "...", "specs": {...}}`
- Platform provisions the environment, installs Anima Machina, pushes config, starts the child
- Child appears on the multi-agent dashboard
- No new URL exposed to the sandbox

### Step 6: PRODUCTION READINESS
- JWT auth on all platform API endpoints
- Ultima X integrated as inference option in Anima Machina
- Generic BYOI verified with at least 2 providers (Conway + one other or mock)
- x402 real payment implementation (not stubs)
- Final cleanup: `grep -ri "miro\|fish\|oasis\|camel"` across codebase — zero results except LICENSE/NOTICE
- Security audit: nothing leaks from sandbox to platform

## NAMING
- **Anima** = individual autonomous agent
- **Anima Machina** = agent framework (CAMEL fork, fully rebranded)
- **Ultimus** = prediction/simulation engine (built on Anima Machina, proprietary)
- **Ultima X** = inference model (Qwen 3.5-122B fork, Apache-2.0)
- **Dimensions** = God's-eye view (simulation + live)
- **Platform** = React dashboard + FastAPI API

## WALLET ARCHITECTURE
- Core wallet: private, holds real funds, visible on USER's dashboard (QR + address + balance), never shared with other agents or publicly
- Public wallet: disposable, created on-demand for receiving external payments, swept to core periodically
- Code-level enforcement: no tool function exposes core wallet address to the agent. The agent uses `send_payment(to, amount)` which signs internally. The agent uses `share_wallet_address()` which returns only the public wallet.
- Dashboard shows core wallet (for the user). Sandbox tools only expose public wallet (for external parties).

## SECURITY
1. Sandbox gets WEBHOOK_URL only (not platform base URL). Per-agent token.
2. Each Anima owns its private key — never transmitted, never in MongoDB.
3. Platform can kill any environment at any time.
4. No "camel", "emergent", "mirofish", platform repo paths, or workspace info inside sandbox.
5. TESTING MODE in genesis prompt is TEMPORARY — remove before production.

## CREDENTIALS
- MONGO_URL=mongodb://localhost:27017
- DB_NAME=anima_fund
- TELEGRAM_BOT_TOKEN=8474833303:AAHAhnRoHSIZTEruDu4ic-tPvdzrnTadnrw
- TELEGRAM_CHAT_ID=8613975358
- CONWAY_API_KEY=cnwy_k_Y28Jd-pIvQ4nn6jXe70HB7A8QjDi5j_Z
- Conway sandbox: 47ba9dfd569c96df2663004bd8b73b86 (9 cents remaining — nearly dead)
- Catalyst wallet: 0x922868f5299b584177256F22DDd753D42117E3eD ($3 USDC)
- Emergent supervisor: READONLY, locked to /app/frontend/ and /app/backend/

## DO NOT REPEAT THESE MISTAKES
1. Do not claim work is done without showing evidence (raw command output, screenshots, API responses)
2. Do not build mocks/stubs and call them features
3. Do not defer Ultimus — it IS the product
4. Do not hardcode Conway — BYOI means any provider
5. Do not put platform info in sandboxes
6. Do not focus on Conway sandbox fixes when the product hasn't been built
7. Do not fill dashboard pages with dummy data
8. Do not treat single-agent as the architecture — the platform handles thousands
9. Do not ignore security (platform URL leaked to sandbox previously)
10. Do not rename things without actually renaming them (rebrand means ALL references, not just the folder name)
