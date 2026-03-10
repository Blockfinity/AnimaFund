# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform. Agent runs inside Conway Cloud sandbox, creates its own wallet, must earn $5k before building products (by any means necessary), then $10k before creating the fund.

## Architecture
- **Host**: Dashboard control plane ONLY — no agent execution, no exposure to VM
- **Conway Sandbox**: Agent lives and runs here (engine, wallet, tools, files)
- **Frontend**: React (port 3000), 13 sidebar pages
- **Backend**: FastAPI (port 8001)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (runs INSIDE sandbox)

## Conway Cloud API Coverage (Verified against docs Feb 2026)

### Sandboxes (Linux VMs)
- `POST /v1/sandboxes` — Create sandbox (name, vcpu 1-4, memory_mb 512-8192, disk_gb 1-50, region)
- `GET /v1/sandboxes/:id` — Get sandbox info
- `GET /v1/sandboxes` — List all sandboxes
- `DELETE /v1/sandboxes/:id` — Delete sandbox (204 No Content)

### Command Execution
- `POST /v1/sandboxes/:id/exec` — Run shell command → {stdout, stderr, exitCode}
- `POST /v1/sandboxes/:id/code` — Run code block → {result, exitCode}

### Files
- `POST /v1/sandboxes/:id/files` — Upload file (path + content)
- `GET /v1/sandboxes/:id/files?path=` — Download file → {content}
- `GET /v1/sandboxes/:id/files/list?path=` — List files → {files: [...]}

### Web Terminal
- `POST /v1/sandboxes/:id/terminal-session` — Create session → {terminal_url, token, expires_at}
- 30-day sliding TTL, treat terminal_url like a password

### PTY Sessions (Interactive Pseudo-Terminals)
- `POST /v1/sandboxes/:id/pty` — Create PTY (command, cols, rows) → {session_id, state}
- `POST /v1/sandboxes/:id/pty/:sessionId/write` — Write input (\\n for Enter, \\x03 for Ctrl+C)
- `GET /v1/sandboxes/:id/pty/:sessionId/read` — Read output (full=true for scrollback)
- `POST /v1/sandboxes/:id/pty/:sessionId/resize` — Resize (cols, rows)
- `DELETE /v1/sandboxes/:id/pty/:sessionId` — Close session
- `GET /v1/sandboxes/:id/pty` — List all active sessions

### Ports
- `POST /v1/sandboxes/:id/ports?port=N&subdomain=X` — Expose → {port, public_url, custom_url}
- URL format: `https://{port}-{short_id}.life.conway.tech`
- Custom subdomains: `https://{subdomain}.life.conway.tech`
- `DELETE /v1/sandboxes/:id/ports/:port` — Unexpose port

### MCP Tools (via Conway Terminal inside sandbox)
- **Sandbox**: sandbox_create, sandbox_list, sandbox_exec, sandbox_write_file, sandbox_read_file, sandbox_expose_port, sandbox_delete, sandbox_get_url
- **PTY**: sandbox_pty_create, sandbox_pty_write, sandbox_pty_read, sandbox_pty_close, sandbox_pty_list
- **Inference**: chat_completions (GPT, Claude, Gemini, Kimi, Qwen)
- **Domains**: domain_search, domain_list, domain_info, domain_register, domain_renew, domain_dns_list/add/update/delete, domain_pricing, domain_check, domain_privacy, domain_nameservers
- **Credits**: credits_balance, credits_history, credits_pricing
- **x402 Payments**: wallet_info, wallet_networks, x402_discover, x402_check, x402_fetch

### Tool Installation (all inside sandbox VM)
- Conway Terminal: `curl -fsSL https://conway.tech/terminal.sh | sh` — auto-creates wallet + API key + configures MCPs
- OpenClaw MCP config: `{"mcpServers": {"conway": {"command": "conway-terminal", "env": {"CONWAY_API_KEY": "..."}}}}`
- Claude Code MCP: `claude mcp add conway conway-terminal -e CONWAY_API_KEY=...`

## UI Architecture
- Single "Anima VM" page with collapsing stepper + 7 monitor tabs
- Stepper: Create Sandbox → Install Terminal → Install OpenClaw → Install Claude Code → Load Skills → Deploy Agent
- Tabs: Live Feed, Terminal (web terminal iframe + PTY sessions), Exec Log, Agent Logs, Browsing, VMs, Message
- PTY session management: Create bash/python3/node sessions, read/write, tab switching
- Multi-agent: Header dropdown selector + CreateAgentModal

## 4-Phase System
| Phase | Objective | Restrictions |
|---|---|---|
| 0 | Test ALL 15 tools | No goals, no business |
| 1 | Earn $5,000 by any means | No products, no fund |
| 2 | Earn $10,000 | No fund |
| 3 | Create the Fund | Full autonomy |

## Testing: 8 iterations, all 100% pass rate (29 backend tests in latest)

## Completed Work
- Security breach remediation
- Deploy-to-sandbox architecture
- Comprehensive tooling (Conway Terminal, OpenClaw, Claude Code)
- Mechanical 4-phase enforcement
- UI/UX Refactor: merged into single Anima VM page with collapsing stepper
- Real-time embedded web terminal (iframe)
- Full PTY API (create/write/read/resize/close/list)
- Port URL endpoint
- Full Conway docs audit verification (Feb 2026)

## Backlog
### P0: Fund Conway credits → full end-to-end provisioning test
### P1: End-to-end phase progression testing
### P2: Smart contracts, Android device control, self-hosted engine
