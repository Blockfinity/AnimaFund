# Anima Platform — Product Requirements

## Product
A platform to launch, monitor, and manage fully autonomous AI agents (Animas) in sandboxed environments. Users define goals via genesis prompts or Ultimus-generated predictions. Animas operate with full autonomy.

## Core Components
- **Anima** — autonomous agent instance
- **Anima Machina** — agent framework (CAMEL fork, Apache-2.0). Runs on platform AND in sandboxed environments. 50+ native toolkits + 3 custom (Wallet, Spawn, StateReporting).
- **Ultimus** — prediction/simulation engine built on Anima Machina. CORE product.
- **Dimensions** — God's-eye view. Observe/chat/inject variables.
- **Platform** — React dashboard + FastAPI API. Thin control plane.

## Current State (March 2026)

### Completed
- Step 1 (CLEAN): 448MB bloat deleted, 4,100 lines dead code archived, engine/ directory with assets
- Step 2 (Anima Machina): CAMEL cloned, 3 custom toolkits (Wallet generates REAL wallets on Base, StateReporting pushes to dashboard, Spawn endpoint created)
- Platform integration: monitor.py replaces 3 old routers, per-agent state store (cache + MongoDB), webhook pipeline working
- Dashboard LIVE: AgentMind page shows real-time agent tool calls, errors, engine status = RUNNING, turns counting, wallet displayed
- Real agent test: The Catalyst ran autonomously, called 10 tools (wallet creation, balance check on Base mainnet $3 USDC, market analysis, DeFi scanning), all visible on dashboard

### What's Real vs Mock
- REAL: Wallet generation (eth-account), balance checks (web3.py against Base mainnet), state reporting to dashboard
- REAL: Dashboard showing live agent data — tool calls, errors, engine status, turns
- ENDPOINT EXISTS but not wired to provisioning: Spawn API (/api/spawn/request) — records requests in MongoDB but doesn't actually provision environments
- NOT IMPLEMENTED: x402 payments (wallet can check balances but can't pay/charge)
- NOT IMPLEMENTED: Generic BYOI (provision.py still has Conway if/else)
- NOT IMPLEMENTED: Sandbox deployment (agents run in-process on platform server, not in isolated VMs)

### Next Priority
1. x402 payment capability in WalletToolkit (pay for services, charge for services)
2. Generic BYOI provisioning (test with mock provider + Conway)
3. Deploy agent to sandbox (install Anima Machina in VM, push genesis prompt, observe via dashboard)
4. Multi-agent: 3+ agents in separate sandboxes, all reporting to dashboard

### Future
- Ultimus (predictor, calculator, executor, Dimensions, 4 seed data modes)
- Multi-Anima economics (treasury, spawn chains, self-sustaining)
- Rebrand camel -> anima_machina
- Your Network integration
