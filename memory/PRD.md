# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed VM/container on the live internet.

## Architecture: Platform vs Agents
- **PLATFORM** = React frontend + FastAPI backend + MongoDB. Standard web app.
- **AGENTS** = Autonomous AIs. Each runs inside its own remote sandbox (Conway VM or Fly.io container).

## BYOI: Bring Your Own Infrastructure
Pluggable provider layer — each provider has its own API key panel:
- **Conway Cloud** — Full VMs with wallet, x402 payments, domains
- **Fly.io** — Fast containers on global edge (native /exec API, node:22 image)
- Provider + key selected per-agent on Genesis screen

## Full 6-Step Provisioning (Verified on Fly.io)
| Step | What it does | Time |
|------|-------------|------|
| 1. Create Sandbox | Provisions VM/container | ~2s |
| 2. Install Terminal | System tools + Node.js + Conway Terminal | ~43s |
| 3. Install OpenClaw | Browser agent + MCP bridge | ~69s |
| 4. Install Claude Code | Self-modification + Conway MCP | ~160s |
| 5. Load Skills | 96 skills pushed to sandbox | ~121s |
| 6. Deploy Agent | Genesis prompt + engine + webhook daemon | ~110s |

- Auto-cascade: clicking Run cascades through ALL remaining steps
- Real-time output with timestamps
- "Run All" button

## What's Been Implemented
- [x] Platform-Agent separation (MongoDB only, no host filesystem)
- [x] Pluggable sandbox provider (Conway + Fly.io)
- [x] Per-provider API key management (editable)
- [x] Auto-cascade provisioning
- [x] Real-time step output
- [x] FULL 6-STEP PROVISIONING VERIFIED ON FLY.IO
- [x] Engine running inside Fly Machine
- [x] 96 skills loaded, Conway Terminal 2.0.9, Claude Code 2.1.73

## P1: Upcoming
- Agent infra-awareness (reimburse creator for non-Conway providers)
- Real smart contracts
- Multiple VMs per agent

## P2: Future/Backlog
- Additional providers (E2B, DigitalOcean, Hetzner)
- Android device control
- Self-hosted agent engine
