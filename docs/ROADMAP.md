# Anima Platform — Project Roadmap

## Step 1: FINISH CLEAN (partially done)
**Goal:** Clean repo, working platform shell.

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Delete automaton/ bloat (dist, native, node_modules, src, packages) | DONE | 448MB freed |
| 1.2 | Move skills + templates to engine/ | DONE | 96 skills, genesis-prompt, constitution |
| 1.3 | Archive dead code | DONE | agent_setup, engine_bridge, payment_tracker, sandbox_poller, webhook_daemon |
| 1.4 | Delete sandbox_provider.py | TODO | Conway-specific, replaced by providers/ |
| 1.5 | Create anima-machina/ placeholder | TODO | For Step 2 |
| 1.6 | Verify backend + frontend working | DONE | All endpoints responding |

## Step 2: CLONE CAMEL -> ANIMA MACHINA
**Goal:** Working agent framework with wallet, spawn, state reporting toolkits.

| # | Task | Dependencies |
|---|---|---|
| 2.1 | git clone camel-ai/camel -> /app/anima-machina/ | 1.5 |
| 2.2 | Full rebrand: camel -> anima_machina | 2.1 |
| 2.3 | Remove telemetry, unused modules | 2.2 |
| 2.4 | Add wallet toolkit (web3.py + x402) | 2.2 |
| 2.5 | Add spawn toolkit (request environments from platform) | 2.2 |
| 2.6 | Add state reporting toolkit (push state to platform webhook) | 2.2 |
| 2.7 | Test: agent with BrowserToolkit + TerminalToolkit on platform server | 2.3 |

## Step 3: CONNECT PLATFORM TO ANIMA MACHINA
**Goal:** Provisioning works, dashboard shows real data from Anima Machina agents.

| # | Task | Dependencies |
|---|---|---|
| 3.1 | Rewrite provision.py: truly generic BYOI, invisible to user | 2.7 |
| 3.2 | Rewrite monitor.py: read from Anima Machina (replaces genesis.py + live.py + infrastructure.py) | 2.7 |
| 3.3 | Connect AgentMind page to real data | 3.2 |
| 3.4 | Connect AnimaVM page to real data | 3.2 |
| 3.5 | Connect Financials page to real data | 3.2 |
| 3.6 | Connect Infrastructure page to real data | 3.2 |
| 3.7 | Connect Activity, Memory, Skills pages | 3.2 |
| 3.8 | Connect SSE pipeline to Anima Machina state updates | 3.2 |
| 3.9 | Test: deploy agent, verify ALL dashboard pages show real data | 3.3-3.8 |

## Step 4: BUILD ULTIMUS
**Goal:** Working prediction engine with Dimensions (God's-eye view).

| # | Task | Dependencies |
|---|---|---|
| 4.1 | Build ultimus/predictor.py (multi-agent simulation) | 2.7 |
| 4.2 | Build ultimus/calculator.py (cost/infrastructure analysis) | 4.1 |
| 4.3 | Build ultimus/executor.py (hands specs to Anima Machina) | 4.1, 3.1 |
| 4.4 | Build ultimus/knowledge.py (GraphRAG) | 2.7 |
| 4.5 | Build ultimus/personas.py (persona generation) | 4.4 |
| 4.6 | Build ultimus/dimensions.py (God's-eye view API) | 4.1 |
| 4.7 | Build all 4 seed data modes (Quick/Deep/Expert/Iterative) | 4.1 |
| 4.8 | Build frontend: goal input, simulation progress, Dimensions, cost review, execute | 4.1-4.7 |
| 4.9 | Test: goal -> simulate -> Dimensions -> execute -> Animas deploy -> results feed back | 4.8 |

## Step 5: MULTI-ANIMA + ECONOMICS
**Goal:** Animas spawn children, manage wallets, achieve self-sustaining economy.

| # | Task | Dependencies |
|---|---|---|
| 5.1 | Spawn API: Animas request new environments | 3.1 |
| 5.2 | Treasury: per-node budget management | 5.1 |
| 5.3 | Wallet/x402: pay for services, charge for services, earn revenue | 2.4 |
| 5.4 | Multi-Anima dashboard: all Animas, wallets, parent-child lineage | 3.2, 5.1 |
| 5.5 | Self-sustaining economics in predictions | 4.2, 5.3 |
| 5.6 | Test: prediction deploys 10+ Animas, they operate, earn, spawn, achieve goal | 5.1-5.5 |

## Step 6: YOUR NETWORK
**Goal:** Agents use your infrastructure and inference.

| # | Task | Dependencies |
|---|---|---|
| 6.1 | Your infra as BYOI provider | 3.1 |
| 6.2 | Your inference as routing option | 3.1 |
| 6.3 | Animas deploy nodes on your network | 6.1 |

## Definition of Done (per step)
- Step 1: Backend starts, frontend loads, repo clean
- Step 2: Anima Machina agent runs on platform server with toolkits
- Step 3: All dashboard pages show real data from running Anima Machina agents
- Step 4: Goal -> simulate -> Dimensions -> execute -> real Animas deploy
- Step 5: 10+ Animas operating, earning, spawning, self-sustaining
- Step 6: Animas on your network
