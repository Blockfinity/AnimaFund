# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via Conway Cloud.

## Architecture
- **Frontend**: React (port 3000), 13 pages + sidebar navigation
- **Backend**: FastAPI (port 8001), routers: genesis, live, openclaw, agents, conway, infrastructure, telegram
- **Database**: MongoDB (anima_fund) — clean, no stale data
- **Agent Engine**: Conway Automaton (TypeScript → dist/bundle.mjs)
- **Integrations**: Conway Cloud API, OpenClaw, Telegram Bot (@AnimaFundbot), Base chain (USDC/ETH)
- **Real-time**: Server-Sent Events (SSE) via /api/live/stream

## Mechanical Boot Sequence (can't be skipped by LLM)
```
start_engine.sh
  → bootstrap_agent.sh
    → PHASE 1: apt-get install curl git wget jq node
    → PHASE 2: npm install -g conway-terminal
    → PHASE 3: install openclaw + configure MCP
    → PHASE 4: FUNCTIONAL TESTS (each tool actually used)
    → PHASE 5: writes BOOT_REPORT.md
    → PHASE 6: sends Telegram boot report
  → Engine starts (bundle.mjs)
    → system-prompt.ts reads BOOT_REPORT.md
    → INJECTS into LLM system prompt (LLM sees it without cat)
    → Wakeup prompt references boot report
    → LLM proceeds: verify balance → Telegram → mission
```

## Key Fixes Applied
1. **Boot sequence**: Mechanical — bootstrap script installs/tests tools before LLM wakes up
2. **Boot report injection**: BOOT_REPORT.md injected directly into LLM system prompt context
3. **Wakeup prompts**: Modified to reference boot report, not "check goals"
4. **Telegram rate limiting**: 3s minimum between sends, milestones only (not every turn)
5. **SSE replaces polling**: Single EventSource connection replaces 16 setInterval polls
6. **Stale data purged**: All preview wallets, test agents, mock DB data removed
7. **Credits display**: Multiple fallback sources, Conway API with 8s timeout

## Screens (13 pages)
| Screen | Status |
|---|---|
| Fund HQ | SSE-connected |
| Agent Mind | SSE-connected |
| Agents | SSE-connected |
| Infrastructure | SSE-connected |
| OpenClaw VM | SSE-connected |
| Skills | SSE-connected |
| Deal Flow | SSE-connected |
| Portfolio | SSE-connected |
| Financials | SSE-connected |
| Activity | SSE-connected |
| Memory | SSE-connected |
| Configuration | Working |
| Engine Console | SSE-connected |

## Remaining Tasks

### P0 (Critical)
- Deploy and verify agent completes boot sequence on production
- Verify Telegram receives boot report message
- Verify credits display with real balance

### P1 (High)
- Monitor first 10 turns for loop behavior
- Verify SOUL.md stays compact (<800 chars)

### P2 (Medium)
- Real smart contracts (ERC-8004)
- Android device control
- Self-hosted agent engine
- Multi-agent communication dashboard
