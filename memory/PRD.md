# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform. Agent runs inside Conway Cloud sandbox, creates its own wallet, must earn $5k before building products (by any means necessary), then $10k before creating the fund.

## Architecture
- **Host**: Dashboard control plane ONLY — no agent execution, no credential exposure to VM
- **Conway Sandbox**: Agent lives and runs here (engine, wallet, tools, files)
- **Frontend**: React (port 3000), 13 sidebar pages
- **Backend**: FastAPI (port 8001)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (runs INSIDE sandbox only)

## Security Architecture (Hardened Mar 2026)
- Agent operates EXCLUSIVELY inside Conway Cloud sandbox VM
- Host credentials (MONGO_URL, DB_NAME) are NEVER exposed to the sandbox
- Only needed secrets injected at deploy: CONWAY_API_KEY, TELEGRAM_*, CREATOR_WALLET
- Genesis prompt explicitly forbids localhost/127.0.0.1 access
- ClawHub skill vetting required (ClawHavoc incident: 340+ malicious skills)
- All skill installs happen INSIDE sandbox via `npx clawhub@latest install`

## Conway Cloud API Coverage (Verified Mar 2026)
### Cloud (Sandboxes)
- Sandboxes: Create, Get, List, Delete
- Execution: Exec command, Run code
- Files: Upload, Download, List
- Web Terminal: Create session (iframe-embeddable)
- PTY: Create, Write, Read, Resize, Close, List
- Ports: Expose (with subdomain), Unexpose, Get URL

### Compute (Inference)
- `POST https://inference.conway.tech/v1/chat/completions`
- Models: gpt-5.2, gpt-5.2-codex, gpt-5-mini, gpt-5-nano, claude-opus-4.6, claude-sonnet-4.5, claude-haiku-4.5, gemini-2.5-pro, gemini-3-pro, gemini-3-flash, kimi-k2.5, qwen3-coder

### Domains (api.conway.domains)
- **Public (no auth)**: Search, Check, Pricing
- **Authenticated (SIWE wallet auth via sandbox)**: List, Register, Renew, DNS CRUD, Privacy, Nameservers, Info, Transactions

## Skills Pipeline (Fixed Mar 2026)
### Provisioning Flow (all inside sandbox):
1. `load-skills` pushes local SKILL.md to `~/.openclaw/skills/` (OpenClaw-compatible path)
2. Runs `npx clawhub@latest install <skill>` inside sandbox for each priority skill
3. Writes `~/.openclaw/skills-manifest.json` with discovery commands and install status
4. Nudges agent with installed skills info and ClawHub search instructions

### Skill Sources (inside sandbox):
- **OpenClaw built-in**: 53 bundled skills (auto-loaded)
- **ClawHub**: 3,000+ community skills at clawhub.ai
- **Conway Terminal**: 42+ MCP tools (auto-available when installed)
- **Local customs**: Skills pushed from host during provisioning

### Discovery Commands (agent uses inside sandbox):
- `openclaw skills list` / `openclaw skills check`
- `npx clawhub search "<query>"` / `npx clawhub@latest install <skill>`
- `cat ~/.openclaw/skills-manifest.json`

## 4-Phase System
| Phase | Objective | Restrictions |
|---|---|---|
| 0 | Test ALL 15 tools (uses gpt-5-nano) | No goals, no business |
| 1 | Earn $5,000 by any means | No products, no fund |
| 2 | Earn $10,000 | No fund |
| 3 | Create the Fund (hundreds of millions target) + Use boardy.ai | Full autonomy |

## Testing: 12 iterations, all 100% pass rate
- Iteration 12 (Mar 2026): Skills pipeline rewrite + security hardening — 19/19 backend, 100% frontend
- Iteration 11 (Mar 2026): Conway domains API alignment — 19/19 backend, 100% frontend
- Iteration 10 (Mar 2026): Full regression after genesis prompt update — 25/25 backend, 100% frontend

## Completed Work (Latest Session — Mar 2026)
1. **Conway Domains API alignment**: Rewrote domain endpoints for correct base URL, params, auth routing
2. **Compute model list update**: Genesis prompt updated to current Conway Compute models
3. **Skills pipeline rewrite**: Fixed path (~/.openclaw/skills/), actual ClawHub install in sandbox, skills-manifest.json
4. **Genesis prompt SKILL DISCOVERY section**: Real commands for OpenClaw/ClawHub skill management
5. **Security hardening**: Localhost access forbidden, skill vetting instructions, ClawHavoc warning

## Backlog
### P0: Fund Conway credits → full end-to-end provisioning test with real sandbox
### P1: End-to-end phase progression testing with real Conway sandbox
### P2: Smart contracts, Android device control, self-hosted engine
