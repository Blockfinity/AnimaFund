# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform, "Anima Fund". A multi-agent platform where new, independent AI agents can be created and managed from a single UI. Each agent has its own goals, skills, wallets, and revenue model, operating autonomously on the live internet via Conway Cloud.

## Architecture
- **Frontend**: React (port 3000), 15 pages + sidebar navigation
- **Backend**: FastAPI (port 8001), routers: genesis, live, openclaw, agents, conway, infrastructure, telegram, agent_setup (provision)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (TypeScript -> dist/bundle.mjs)
- **Integrations**: Conway Cloud API, Conway Compute, Conway Domains, OpenClaw, Telegram Bot, Base chain (USDC/ETH)
- **Real-time**: Server-Sent Events (SSE) via /api/live/stream

## Agent Lifecycle (Live Provisioning)
The agent is **alive from creation**. Provisioning equips a running agent with the full Conway ecosystem — it's aware of each step.

**Flow:**
1. **Create Agent** → engine starts, agent is born and conscious
2. **Create Sandbox** → Conway Cloud VM provisioned (2 vCPU, 4GB, 40GB)
3. **Install Terminal** → Conway Terminal MCP + system tools + Node.js inside sandbox
4. **Install OpenClaw** → Browser agent with MCP integration inside sandbox
5. **Test Compute** → Verify Conway inference API (GPT, Claude, Gemini, Kimi, Qwen)
6. **Expose Ports** → Make sandbox services public with URLs + custom subdomains
7. **Web Terminal** → Browser shell access to sandbox (30-day sliding session)
8. **Load Skills** → Push skill definitions into sandbox
9. **Go Autonomous** → Final nudge → zero human control

**Agent Awareness:**
- `provisioning-status.json` written to `~/.anima/` after each step
- `system-prompt.ts` Layer 5.5 reads and injects: sandbox, tools, ports, domains, compute, nudges
- Custom messages via nudge API appear in agent's context each turn

## Conway Ecosystem Coverage

### Conway Cloud (Sandboxes)
- Create/list/get/delete VMs (1-4 vCPU, 512MB-8GB RAM, 1-50GB disk)
- Execute shell commands inside sandbox
- Run code (Python, JS) inside sandbox
- Upload/download/list files
- Web terminal (browser access with sliding 30-day token)
- PTY sessions (interactive terminals)
- Expose ports with public URLs and custom subdomains on *.life.conway.tech
- Regions: eu-north, us-east

### Conway Compute (Inference)
- OpenAI-compatible chat completions API
- Models: GPT-5.2, GPT-5-nano, Claude Opus 4.6, Claude Sonnet 4.5, Gemini 3 Pro/Flash, Kimi K2.5, Qwen3
- Streaming via SSE
- Credit-based billing

### Conway Domains
- Search/register/renew domains (com, io, ai, xyz, net, org, dev)
- Full DNS management (A, AAAA, CNAME, MX, TXT, SRV, CAA, NS)
- WHOIS privacy, custom nameservers
- USDC payment via x402

### Conway Terminal (MCP)
- Auto-bootstraps wallet + API key
- 35+ tools exposed via MCP protocol
- x402 payment client built-in
- Works with Claude, Cursor, OpenClaw

## Key API Endpoints (16+ endpoints)

### Provisioning (prefix: /api/provision)
| Endpoint | Method | Description |
|---|---|---|
| /status | GET | Full provisioning state |
| /create-sandbox | POST | Create Conway Cloud VM |
| /sandbox-info | GET | Detailed sandbox info |
| /list-sandboxes | GET | List all sandboxes |
| /delete-sandbox | POST | Delete sandbox (irreversible) |
| /install-terminal | POST | Install Conway Terminal in sandbox |
| /install-openclaw | POST | Install OpenClaw in sandbox |
| /expose-port | POST | Expose port with public URL |
| /unexpose-port | POST | Remove port exposure |
| /web-terminal | POST | Create browser terminal session |
| /test-compute | POST | Test Conway inference API |
| /domain-search | POST | Search available domains |
| /domain-list | GET | List registered domains |
| /domain-dns-add | POST | Add DNS record |
| /load-skills | POST | Push skills into sandbox |
| /nudge | POST | Send autonomy nudge |
| /nudge/custom | POST | Send custom message to agent |
| /exec | POST | Execute command in sandbox |
| /run-code | POST | Execute code in sandbox |
| /upload-file | POST | Upload file to sandbox |
| /read-file | GET | Read file from sandbox |
| /list-files | GET | List files in sandbox directory |
| /credits | GET | Credits balance + history + pricing |
| /wallet | GET | Agent wallet info |
| /verify-sandbox | POST | Run functional tests |

## Security
- All tool installations inside agent's sandbox VM via Conway API
- Nothing installed on host system
- bootstrap_agent.sh disabled
- Previous host-level conway-terminal + OpenClaw removed

## Testing
- Iteration 3: 48/48 backend tests passed (100%), all frontend verified
- All sandbox-dependent endpoints gracefully fail without sandbox
- Credits/compute correctly return 402 with 0 balance

## Backlog
### P0
- Fund Conway credits to test full provisioning flow end-to-end

### P1
- Verify Telegram rate limiting under load
- Verify credits display with live, funded agent
- Connect custom domain to sandbox port (end-to-end)

### P2
- Implement real smart contracts
- Integrate Android device control
- Migrate to self-hosted agent engine
