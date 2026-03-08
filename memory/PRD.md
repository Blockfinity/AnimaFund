# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform. Multiple independent AI agents, each with own wallet/goals/skills, operating autonomously on the live internet via Conway Research ecosystem.

## Architecture
```
/app
├── automaton/genesis-prompt.md  # Ultra-lean template (1.7KB, 20 lines)
├── backend/routers/
│   ├── agents.py       # Agent CRUD, bootstrap, push-genesis, isolation
│   ├── genesis.py      # Status, logs, wallet, prompt template
│   ├── live.py         # Live turns, soul, identity, messages
│   ├── infrastructure.py # VMs, terminal, domains, tools, activity feed
│   └── telegram.py     # Telegram relay
├── frontend/src/pages/
│   ├── AgentMind.js    # Real-time monitoring (stable polling, 14 log tags)
│   ├── Infrastructure.js # 6-tab infra dashboard
│   ├── Activity.js     # Comprehensive categorized feed
│   └── [FundHQ, Agents, Skills, etc.]
└── scripts/
    ├── start_engine.sh     # Bootstrap + engine start
    └── bootstrap_agent.sh  # Conway Terminal + OpenClaw pre-install
```

## Per-Agent Environment
```
~/agents/{id}/
├── .anima/          # Engine data (wallet, config, state.db, auto-config, genesis-prompt)
├── .automaton/      # Symlink → .anima (backward compat)
├── .conway/         # Conway Terminal config (synced from bootstrap)
└── .openclaw/       # OpenClaw config (points to Conway Terminal MCP)
```

## Completed (All Tested)
- [x] UI stability fix (viewRef pattern, content-based comparison)
- [x] Genesis prompt: 490 lines → 20 lines. Priority 1 = condense SOUL.md
- [x] Agent bootstrap: Conway Terminal + API key + OpenClaw pre-installed
- [x] Directory alignment: .anima primary, .automaton symlink
- [x] auto-config.json: proper creator address
- [x] Infrastructure page: 6 tabs (Overview, Sandboxes, Terminal, Domains, Tools, Network)
- [x] Activity feed: ALL actions categorized with filters
- [x] Live Feed: 14 log tags (TOOL, ORCH, SANDBOX, NETWORK, FINANCE, etc.)
- [x] Push-genesis endpoint: update existing agents without recreation
- [x] Model names: GPT-5.2, Claude Opus 4.6, Gemini 3, Kimi K2.5, Qwen3
- [x] Security audit: no exposed secrets, env-only config
- [x] Deployment readiness: all checks pass

## Testing
- Iteration 37: 32/32 pass (UI stability)
- Iteration 38: 28/28 pass (Infrastructure)
- Iteration 39: 52/52 pass (Deployment readiness)
- Deployment agent: PASS

## Next (Post-Deployment)
- [ ] Test live agent with ultra-lean prompt (should condense SOUL.md on turn 1)
- [ ] Verify sandbox data flows to Infrastructure page
- [ ] Backend Telegram auto-relay for infra events

## Backlog
- [ ] Real smart contracts
- [ ] Android device control
- [ ] Self-hosted infrastructure
- [ ] React Query/SWR polling migration
