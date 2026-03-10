# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform. Agent runs inside Conway Cloud sandbox, creates its own wallet, must earn $5k before building products (by any means necessary), then $10k before creating the fund.

## Architecture
- **Host**: Dashboard control plane ONLY — no agent execution, no exposure to VM
- **Conway Sandbox**: Agent lives and runs here (engine, wallet, tools, files)
- **Frontend**: React (port 3000), 13 sidebar pages
- **Backend**: FastAPI (port 8001)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (runs INSIDE sandbox only)

## Multi-Agent Data Isolation (Fixed Feb 2026)
- Each agent gets its own provisioning-status.json at `~/agents/{agent_id}/.anima/`
- Default agent (anima-fund) uses `~/.anima/provisioning-status.json`
- Active agent tracked via `/tmp/anima_active_agent_id` (persisted across restarts)
- When switching agents via Header dropdown, all provisioning endpoints automatically serve that agent's data
- `/api/provision/status` now includes `agent_id` field confirming which agent's data is shown

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
- Auth: Conway API key bearer

### Domains (api.conway.domains)
- **Public (no auth)**: Search (`/domains/search?q=`), Check (`/domains/check?domains=`), Pricing (`/domains/pricing?tlds=`)
- **Authenticated (SIWE wallet auth via sandbox)**: List, Register (x402 USDC), Renew, DNS CRUD, Privacy toggle, Nameservers, Domain Info, Transactions
- Dashboard routes authenticated ops through sandbox exec (Conway Terminal handles wallet auth)

## 4-Phase System
| Phase | Objective | Restrictions |
|---|---|---|
| 0 | Test ALL 15 tools (uses gpt-5-nano for compute test) | No goals, no business |
| 1 | Earn $5,000 by any means | No products, no fund |
| 2 | Earn $10,000 | No fund |
| 3 | Create the Fund (hundreds of millions target) + Use boardy.ai | Full autonomy |

## API Endpoints Summary
### Provisioning (per-agent, parameterized)
- `POST /api/provision/{agent_id}/create-sandbox`
- `POST /api/provision/{agent_id}/install-terminal`
- `POST /api/provision/{agent_id}/deploy-agent`
- `GET /api/provision/{agent_id}/status`
- PTY: create, write, read, resize, close, list

### Domains (public — direct to api.conway.domains)
- `POST /api/provision/domain-search`
- `POST /api/provision/domain-check`
- `GET /api/provision/domain-pricing`

### Domains (authenticated — routed via sandbox)
- `GET /api/provision/domain-list`
- `POST /api/provision/domain-register`
- `POST /api/provision/domain-renew`
- `GET /api/provision/domain-dns-list`
- `POST /api/provision/domain-dns-add`
- `PUT /api/provision/domain-dns-update`
- `DELETE /api/provision/domain-dns-delete`
- `PUT /api/provision/domain-privacy`
- `PUT /api/provision/domain-nameservers`
- `GET /api/provision/domain-info`
- `GET /api/provision/domain-transactions`

### Agents
- `POST /api/agents/` (Create)
- `GET /api/agents/` (List)
- `POST /api/agents/{id}/select` (Switch active)
- `GET /api/agents/{id}/skills` (Get skills)

## Testing: 11 iterations, all 100% pass rate
- Iteration 11 (Mar 2026): Conway docs alignment — domains API rewrite + model list update — 19/19 backend, 100% frontend
- Iteration 10 (Mar 2026): Full regression after genesis-prompt.md update — 25/25 backend, 100% frontend

## Completed Work (Latest)
- **Conway Domains API alignment (Mar 2026)**: Rewrote all domain endpoints to use correct base URL (api.conway.domains), correct params (q= not query=), proper auth routing (public direct, authenticated via sandbox). Added 9 new endpoints.
- **Model list update (Mar 2026)**: Genesis prompt and skills list updated from outdated GPT-4o to current gpt-5.2/gpt-5-nano models matching Conway Compute docs.
- Genesis prompt Phase 3 with boardy.ai and hundreds of millions fund target
- UI/UX Refactor: single Anima VM page with collapsing stepper
- Per-agent provisioning isolation
- Full Conway PTY API implementation
- Telegram Bot integration

## Backlog
### P0: Fund Conway credits → full end-to-end provisioning test with real sandbox
### P1: End-to-end phase progression testing with real Conway sandbox
### P2: Smart contracts, Android device control, self-hosted engine
