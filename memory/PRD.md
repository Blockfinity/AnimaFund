# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform. Multi-agent platform where AI agents are created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via Conway Cloud.

## Core Architecture
- **Host (Emergent platform)**: Dashboard control plane only — no agent execution on host
- **Conway Sandbox**: Where the agent actually lives and runs (engine, wallet, tools)
- **Frontend**: React (port 3000), 15 pages + sidebar
- **Backend**: FastAPI (port 8001), routers: genesis, live, provision, agents, conway, infrastructure, telegram, openclaw
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (TypeScript) — runs INSIDE sandbox
- **Integrations**: Conway Cloud, Conway Compute, Conway Domains, OpenClaw, Telegram Bot, Base chain

## Agent Lifecycle

### Provisioning (User-driven, from dashboard)
1. **Create Sandbox** → Conway Cloud VM (2 vCPU, 4GB, 40GB)
2. **Install Terminal** → Conway Terminal MCP + system tools + Node.js inside sandbox
3. **Install OpenClaw** → Browser agent inside sandbox
4. **Deploy Agent** → Push engine bundle + genesis prompt + config + skills + phase-state.json into sandbox, start engine process

### Phase System (Code-enforced in system-prompt.ts)
| Phase | Objective | Restrictions |
|---|---|---|
| 0 | Test ALL 10 tools functionally | No goals, no business, no products |
| 1 | Earn $5,000 (1 hour) | No products, no fund, no domains, immediate revenue only |
| 2 | Earn $10,000 | No fund creation, may register revenue-generating domains |
| 3 | Create the Fund | Full autonomy — build infrastructure, recruit agents |

### Phase Enforcement
- `genesis-prompt.md`: Explicit phase rules and forbidden actions
- `system-prompt.ts` Layer 5.6: Reads `~/.anima/phase-state.json` every turn, injects current phase + rules
- Wakeup prompt: Instructs agent to read phase-state.json before any action
- Agent updates phase-state.json as it completes phases
- ALL actions reported via Telegram

### 10 Functional Tool Tests (Phase 0)
1. **curl** — Download file, verify size > 100 bytes
2. **git** — Clone repo, verify file exists
3. **node** — Start HTTP server, verify response
4. **python3** — Run hashlib code, verify JSON output
5. **Telegram** — Send message, verify 200 response
6. **Conway Terminal** — wallet_info + check_credits + check_usdc_balance
7. **Sandbox** — Create sub-sandbox, exec command, verify output
8. **Domains** — Search domain availability
9. **Compute** — Run inference, get response
10. **Port Exposure** — Start server, expose port, curl public URL

## Agent's Wallet
- NO host wallet — agent creates its own wallet via Conway Terminal's auto-bootstrap inside sandbox
- Revenue targets checked against USDC wallet balance + Conway credits (both)

## Conway Ecosystem Coverage
- Cloud: Sandboxes, exec, files, web terminal, PTY, port exposure
- Compute: Multi-model inference (GPT, Claude, Gemini, Kimi, Qwen)
- Domains: Search, register, DNS management, WHOIS
- Terminal: 35+ MCP tools, x402 payments, wallet management
- Payments: USDC on Base, credits, x402

## API Endpoints (27+ endpoints under /api/provision)
Status, create-sandbox, sandbox-info, list-sandboxes, delete-sandbox, install-terminal, install-openclaw, expose-port, unexpose-port, web-terminal, test-compute, domain-search, domain-list, domain-dns-add, load-skills, deploy-agent, agent-logs, phase-state, nudge, nudge/custom, exec, run-code, upload-file, read-file, list-files, credits, wallet, verify-sandbox

## Testing
- Iteration 4: 25/25 backend + all frontend = 100% pass rate
- Security: No host installations verified in all iterations

## Backlog
### P0: Fund Conway credits → test full flow end-to-end
### P1: Verify Telegram reporting, end-to-end phase progression
### P2: Smart contracts, Android device control, self-hosted engine
