# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital fund platform. Agent runs inside Conway Cloud sandbox, creates its own wallet, must earn $5k before building products (by any means necessary), then $10k before creating the fund.

## Architecture
- **Host**: Dashboard control plane ONLY — no agent execution
- **Conway Sandbox**: Agent lives and runs here (engine, wallet, tools, files)
- **Frontend**: React (port 3000), 13 sidebar pages
- **Backend**: FastAPI (port 8001)
- **Database**: MongoDB (anima_fund)
- **Agent Engine**: Conway Automaton (runs INSIDE sandbox)

## Agent Wallet
- Created by Conway Terminal auto-bootstrap inside sandbox on install
- Stored at `~/.conway/config.json` inside sandbox
- Ethereum wallet on Base — USDC payments via x402
- This is the ONLY wallet — no host wallet

## Provisioning Flow (Technical Order)
1. Create Sandbox → Conway Cloud VM
2. Install Conway Terminal → auto-creates wallet + API key + configures all MCPs
3. Install OpenClaw → autonomous browser with Conway MCP bridge
4. Install Claude Code → self-modification via MCP
5. Load Skills → push skill definitions into sandbox
6. Deploy Agent → push engine + genesis + config + phase-state.json, start engine

## UI Architecture (Updated Feb 2026)
- **Single "Anima VM" page** replaces old separate "Provision Agent" and "OpenClaw VM" pages
- **Collapsing stepper** at top for provisioning — auto-collapses when all steps done
- **Status bar** with tool status pills and phase indicator
- **6 monitor tabs**: Live Feed, VM Console, Agent Logs, Browsing, VMs, Message
- All provisioning + monitoring in one unified view

## 4-Phase System (Code-Enforced)
| Phase | Objective | Restrictions |
|---|---|---|
| 0 | Test ALL 15 tools functionally | No goals, no business, no revenue |
| 1 | Earn $5,000 by any means | No products, no fund, no domains. Crypto memes, trading, gambling, prediction markets, bounties — anything |
| 2 | Earn $10,000 | No fund. May register revenue-generating domains |
| 3 | Create the Fund | Full autonomy |

## Complete Conway Tool Coverage
- **Sandboxes**: create, list, exec, write_file, read_file, expose_port, get_url, delete, pty_create/write/read/close/list
- **Compute**: chat_completions (GPT, Claude, Gemini, Kimi, Qwen)
- **Domains**: search, check, register, renew, info, pricing, dns_list/add/update/delete, privacy, nameservers
- **Payments**: wallet_info, wallet_networks, x402_discover, x402_check, x402_fetch, credits_balance/history/pricing
- **Browsing**: browse_page, discover_agents, send_message, check_social_inbox
- **Self-mod**: edit_own_file, install_mcp_server, install_skill, create_skill
- **Orchestrator**: create_goal, list_goals, get_plan, orchestrator_status
- **Replication**: spawn_child, list_children, fund_child, message_child
- **Memory**: update_soul, remember_fact, recall_facts, save_procedure, recall_procedure
- **Git**: status, diff, commit, log, push, branch, clone
- **MCP**: Conway Terminal, OpenClaw, Claude Code

## API Endpoints (30+)
All under /api/provision: status, create-sandbox, sandbox-info, list-sandboxes, delete-sandbox, install-terminal, install-openclaw, install-claude-code, expose-port, unexpose-port, web-terminal, test-compute, domain-search, domain-list, domain-dns-add, load-skills, deploy-agent, agent-logs, phase-state, nudge, nudge/custom, exec, run-code, upload-file, read-file, list-files, credits, wallet, verify-sandbox

## Sidebar Navigation (13 items)
1. Anima VM (provisioning + monitoring)
2. Agent Mind
3. Fund HQ
4. Agents
5. Infrastructure
6. Skills
7. Deal Flow
8. Portfolio
9. Financials
10. Activity
11. Memory
12. Configuration
13. Wallet & Logs

## Testing: 6 iterations, all 100% pass rate

## Completed Work
- Security breach remediation (no host installations)
- Deploy-to-sandbox architecture
- Comprehensive tooling integration (Conway Terminal, OpenClaw, Claude Code)
- Mechanical 4-phase enforcement
- **UI/UX Refactor (Feb 2026)**: Merged Provision Agent + OpenClaw VM into single Anima VM page with collapsing stepper

## Backlog
### P0: Fund Conway credits → full end-to-end test
### P1: Real-time monitoring components (live terminal/browser views in VM), Agent selector for multiple agents, End-to-end phase progression
### P2: Smart contracts, Android device control, self-hosted engine, Telegram reporting verification
