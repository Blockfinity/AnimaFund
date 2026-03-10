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

## Agent Creation Flow (Fixed Feb 2026)
1. User clicks "Create New Agent" in Header dropdown
2. CreateAgentModal: name, genesis prompt, goals, Telegram creds, skills, wallets
3. Frontend verifies Telegram (getMe + sendMessage) before backend call
4. Backend stores config + selected_skills in MongoDB (no host engine start)
5. App auto-navigates to AnimaVM page for that agent
6. User provisions via AnimaVM stepper: Sandbox → Terminal → OpenClaw → Claude Code → Skills → Deploy
7. Skills step loads both local skills AND agent-selected priority skills from DB

## Conway Cloud API Coverage (Verified Feb 2026)
- Sandboxes: Create, Get, List, Delete
- Execution: Exec command, Run code
- Files: Upload, Download, List
- Web Terminal: Create session (iframe-embeddable)
- PTY: Create, Write, Read, Resize, Close, List
- Ports: Expose (with subdomain), Unexpose, Get URL

## MCP Tools (42+ tools via Conway Terminal inside sandbox)
- Sandbox, PTY, Inference, Domains, Credits, x402, OpenClaw, Self-modification

## UI Architecture
- Single "Anima VM" page: collapsing stepper + 7 monitor tabs
- Tabs: Live Feed, Terminal (web + PTY), Exec Log, Agent Logs, Browsing, VMs, Message
- Header: Agent selector dropdown + create agent
- Multi-agent: Full data isolation per agent

## 4-Phase System
| Phase | Objective | Restrictions |
|---|---|---|
| 0 | Test ALL 15 tools | No goals, no business |
| 1 | Earn $5,000 by any means | No products, no fund |
| 2 | Earn $10,000 | No fund |
| 3 | Create the Fund | Full autonomy |

## Testing: 9 iterations, all 100% pass rate
- Deployment agent: PASS (ready for Kubernetes)

## Completed Work
- Security breach remediation
- Deploy-to-sandbox architecture
- Comprehensive tooling (Conway Terminal, OpenClaw, Claude Code)
- Mechanical 4-phase enforcement
- UI/UX Refactor: single Anima VM page with collapsing stepper
- Embedded web terminal + PTY sessions
- Full Conway docs audit (all 9 pages verified)
- **Per-agent provisioning isolation (Feb 2026)**
- **Agent creation no longer starts engine on host**
- **Skills flow: creation → DB → provisioning stepper**
- **Deployment verification passed**

## Backlog
### P0: Fund Conway credits → full end-to-end provisioning test with real sandbox
### P1: End-to-end phase progression testing
### P2: Smart contracts, Android device control, self-hosted engine
