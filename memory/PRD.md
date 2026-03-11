# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed VM/container on the live internet.

## Architecture: Platform vs Agents
- **PLATFORM** = React frontend + FastAPI backend + MongoDB. Standard web app.
- **AGENTS** = Autonomous AIs. Each runs inside its own remote sandbox (Conway VM or Fly.io container).

## BYOI: Bring Your Own Infrastructure
Pluggable provider layer — each provider has its own API key panel:
- **Conway Cloud** — Full VMs with wallet, x402 payments, domains
- **Fly.io** — Fast containers on global edge (uses native /exec API, node:22 image)
- Provider + key selected per-agent on Genesis screen
- All provisioning steps work identically regardless of provider

## Provisioning Flow
- Auto-cascade: clicking Run on any step cascades through ALL remaining steps
- Real-time output: each step shows timestamped logs as it runs
- "Run All" button starts from first incomplete step and cascades

## What's Been Implemented
- [x] Platform-Agent separation (MongoDB only, no host filesystem)
- [x] Pluggable sandbox provider (Conway + Fly.io)
- [x] Fly.io: native /exec API, node:22 image, auto-start stopped machines
- [x] Per-provider API key management (Conway key panel + Fly.io token panel)
- [x] Editable keys — click to change either provider's key
- [x] Auto-cascade provisioning steps
- [x] Real-time step output with timestamps
- [x] "Run All" button
- [x] Full E2E verified: Create Sandbox → Install Terminal → all passing on Fly.io
- [x] Deployment ready (lean requirements, .env tracked, safety timeouts)

## P0: Test
- Full 6-step provisioning via Fly.io in production
- Verify agent starts inside Fly Machine

## P1: Upcoming
- Agent infra-awareness (reimburse creator for non-Conway providers)
- Real smart contracts
- Multiple VMs per agent

## P2: Future/Backlog
- Additional providers (E2B, DigitalOcean, Hetzner)
- Android device control
- Self-hosted agent engine
