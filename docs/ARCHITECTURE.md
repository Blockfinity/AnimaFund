# Anima Platform — Architecture (Final)

## WHAT THIS IS

A platform to launch, monitor, and manage fully autonomous AI agents (Animas)
in sandboxed environments. Users define goals, the platform provisions
infrastructure, and Animas operate autonomously to achieve those goals.

## NAMING

- **Anima** — an individual autonomous agent
- **Anima Machina** — the agent framework (forked from CAMEL-AI, Apache-2.0, fully rebranded). Runs BOTH on the platform (for Ultimus simulations) AND inside sandboxed environments (as the agent runtime). Has 50+ native toolkits.
- **Ultimus** — the prediction/simulation engine. Built on Anima Machina. Dashboard screens, not a separate app.
- **Dimensions** — the God's-eye view. Observe simulated or live Animas, chat with them, inject variables. Dashboard screens.
- **Platform** — the React dashboard + FastAPI API. Thin control plane.

## THREE SEPARATE SYSTEMS

### 1. Anima Machina (agent framework — CAMEL fork)
Creates agents. Runs them. Gives them tools, memory, personas, inference. Runs EVERYWHERE:
- On the platform server: powers Ultimus simulations
- Inside sandboxed environments: each Anima is an Anima Machina agent instance

OpenClaw is NOT needed. Anima Machina has all capabilities natively (50+ toolkits).
We ADD: wallet toolkit (x402), spawn toolkit, state reporting toolkit, full rebrand.

### 2. Ultimus (prediction engine — built on Anima Machina)
Three sub-processes: Predictor, Calculator, Executor.
Four seed data modes: Quick/Deep/Expert/Iterative Predict.
Dimensions: God's-eye view for both simulation and live modes.

### 3. Platform (thin control plane)
Provisions environments via BYOI. Monitors Animas. Spawn API. Dimensions. Kill switch.

## CRITICAL PRINCIPLES

1. Animas are fully autonomous within their genesis prompt
2. BYOI is generic — any provider API, not a hardcoded list
3. Provisioning is invisible to users
4. Multiple Animas can share environments or have dedicated ones
5. All Animas are sandboxed — platform can kill any environment
6. Every prediction must be self-sustaining
7. Predictions are non-linear — thousands of paths explored simultaneously
8. Genesis prompts are auto-generated from simulation data
9. The 96 custom skills are for The Catalyst ONLY
10. Ultimus and Anima Machina are SEPARATE systems

## TASK LIST

See **ROADMAP.md** for the authoritative task list and step definitions.

## REPO STRUCTURE (Target)

**NOTE: Supervisor config is READONLY. frontend/ and backend/ paths cannot be renamed.**

```
/app
├── frontend/           <- Dashboard (supervisor locked)
│   └── src/pages/     <- 14 existing + Ultimus/Dimensions screens
│
├── backend/            <- Platform API (supervisor locked)
│   ├── routers/
│   │   ├── agents.py      <- Anima CRUD
│   │   ├── provision.py   <- Generic BYOI provisioning (~200 lines)
│   │   ├── monitor.py     <- Read Anima state from Anima Machina
│   │   ├── spawn.py       <- Environment requests from Animas
│   │   ├── dimensions.py  <- God's-eye view API
│   │   ├── telegram.py    <- Telegram integration
│   │   └── webhook.py     <- Receive Anima state reports
│   └── providers/
│       └── base.py        <- Generic BYOI interface
│
├── engine/             <- Assets pushed to environments
│   ├── skills/        <- 96 custom skills (The Catalyst only)
│   └── templates/     <- Genesis prompts, constitution
│
├── anima-machina/     <- Agent framework (CAMEL fork, Apache-2.0, rebranded)
│
├── ultimus/            <- Prediction engine (built on Anima Machina, proprietary)
│   ├── predictor.py   <- Simulation runner
│   ├── calculator.py  <- Cost/infrastructure analysis
│   ├── executor.py    <- Hands specs to Anima Machina
│   ├── dimensions.py  <- God's-eye view
│   └── api.py         <- REST endpoints
│
├── archive/            <- Reference from old codebase
└── docs/               <- Architecture, security, changelog
```
