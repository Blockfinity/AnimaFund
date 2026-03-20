# Anima Platform — Product Requirements

## ACCEPTANCE TEST: PASSED
Phase 0 complete. The Catalyst operating autonomously in Conway sandbox.
- Agent in sandbox (PID 979832), using Conway inference (gpt-5-mini)
- Telegram: receiving messages from agent
- Dashboard: 20+ actions, status=running, live=true
- Wallet created, balance checked ($3 USDC on-chain)
- Shell, Node, file ops, memory all working
- Agent autonomously installed Playwright for browser capability
- Now executing Phase 1 (revenue strategies)

## Current State (March 2026)

### Working End-to-End
- Anima Machina agent framework (CAMEL fork, 50+ toolkits)
- 3 custom toolkits: Wallet, Spawn, StateReporting
- Conway sandbox deployment via provision.py
- Conway inference from inside sandbox (no external keys)
- Dashboard pipeline: sandbox agent -> webhook -> per-agent store -> monitor.py -> frontend
- Telegram reporting from agent
- Genesis prompt with real credentials (template vars replaced)
- No turn limit (agent runs indefinitely)
- Ultima X package created (Modelfile + config + README + NOTICE)

### Inference Hierarchy
1. Conway compute (sandbox's own key) - current
2. Ultima X self-hosted (user's GPU, zero cost) - packaged, ready for deployment
3. Ultima X on your network (x402 payments) - future
4. External API (user's choice) - supported via llm-key endpoint

### Next Priority
1. Monitor The Catalyst's Phase 1 progress
2. x402 payments (agent needs to pay/charge)
3. Generic BYOI (test with non-Conway provider)
4. Spawn API wired to provisioning
5. Multi-agent dashboard
6. Ultimus (CORE) — predictor, calculator, executor, Dimensions
7. Rebrand camel -> anima_machina

## Architecture
FORK_PROMPT.md = definitive source. ROADMAP.md = task list.
