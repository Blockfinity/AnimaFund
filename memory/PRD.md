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

## Onboarding Flow (Redesigned Mar 2026)
1. New user opens app → Genesis screen shows 6-step provisioning stepper
2. Steps: Create Sandbox → Install Terminal → Install OpenClaw → Claude Code → Load Skills → Create Anima
3. After Install Terminal: wallet created, QR code displayed for funding
4. After Create Anima: agent deployed inside sandbox, "Open Dashboard" button appears
5. Dashboard opens → AnimaVM is monitoring-only (status bar + 7 tabs)
6. Returning users (config_exists=true) skip genesis and go straight to dashboard

## Security Architecture
- Agent operates EXCLUSIVELY inside Conway Cloud sandbox VM
- Host credentials (MONGO_URL, DB_NAME) NEVER exposed to sandbox
- Genesis prompt forbids localhost/127.0.0.1 access
- ClawHub skill vetting required (ClawHavoc incident)
- All skill installs happen INSIDE sandbox

## Conway Cloud API Coverage (Verified Mar 2026)
### Cloud: Sandboxes, Exec, Files, Web Terminal, PTY, Ports
### Compute: inference.conway.tech — gpt-5.2, claude-opus-4.6, gemini-3-pro, kimi-k2.5, qwen3-coder
### Domains (api.conway.domains): Public (search, check, pricing) + Authenticated via sandbox (register, DNS, privacy, nameservers)

## Skills Pipeline
- Skills pushed to `~/.openclaw/skills/` (OpenClaw-compatible path)
- ClawHub installs run inside sandbox via `npx clawhub@latest install`
- Skills manifest at `~/.openclaw/skills-manifest.json`
- Genesis prompt includes SKILL DISCOVERY section with real ClawHub/OpenClaw commands

## 4-Phase System
| Phase | Objective | Restrictions |
|---|---|---|
| 0 | Test ALL 15 tools (uses gpt-5-nano) | No goals, no business |
| 1 | Earn $5,000 by any means | No products, no fund |
| 2 | Earn $10,000 | No fund |
| 3 | Create the Fund (hundreds of millions target) + Use boardy.ai | Full autonomy |

## UI Architecture
- **Genesis/Onboarding screen**: 6-step provisioning stepper + wallet QR + Open Dashboard
- **Dashboard**: Sidebar (13 pages) + Header (agent selector) + Main content
- **AnimaVM page**: Monitoring-only — status bar (5 pills) + 7 tabs (Live Feed, Terminal, Exec Log, Agent Logs, Browsing, VMs, Message)

## Testing: 13 iterations, all 100% pass rate
- Iteration 13 (Mar 2026): Provisioning stepper architectural split — 17/17 tests passed

## Completed Work (This Session — Mar 2026)
1. Conway Domains API alignment (correct base URL, params, auth routing)
2. Compute model list update (current Conway models)
3. Skills pipeline rewrite (correct path, actual ClawHub install, manifest)
4. Genesis prompt SKILL DISCOVERY section + security hardening
5. Deployment readiness (.gitignore fix)
6. **Onboarding redesign**: Provisioning stepper moved from AnimaVM to genesis screen, AnimaVM is now monitoring-only

## Backlog
### P0: Fund Conway credits → full end-to-end provisioning test with real sandbox
### P1: End-to-end phase progression testing with real Conway sandbox
### P2: Smart contracts, Android device control, self-hosted engine
