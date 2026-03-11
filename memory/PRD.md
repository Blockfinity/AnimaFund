# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed VM/container on the live internet.

## Architecture: Platform vs Agents
- **PLATFORM** = React frontend + FastAPI backend + MongoDB. Standard web app deployed normally.
- **AGENTS** = Autonomous AIs built on Automaton. Each runs inside its own remote sandbox (Conway VM or Fly.io container).
- The platform CREATES and MONITORS agents but does NOT run agent logic itself.

## BYOI: Bring Your Own Infrastructure
The platform supports multiple sandbox providers through a pluggable provider layer:
- **Conway Cloud** — Full VMs with wallet, x402 payments, domains
- **Fly.io** — Fast containers on global edge network (tested & working)
- Provider is selected per-agent on the Genesis screen
- All provisioning steps work identically regardless of provider

## Two Prompts
1. **AI VC Fund Prompt** — Pre-loaded for default "anima-fund" founder agent. Just provision & deploy.
2. **Genesis Prompt** — Template for creating additional agents (GPs, analysts, etc.)

## Core Architecture
- **Backend:** FastAPI + MongoDB (single source of truth)
- **State Management:** `agent_state.py` centralizes all MongoDB state access
- **Sandbox Provider:** `sandbox_provider.py` — unified interface for Conway/Fly.io
- **Data Pipeline:** Hybrid (webhook + background poller → SSE → React)

## What's Been Implemented
- [x] Full SSE data pipeline
- [x] Per-agent Conway API key storage in MongoDB
- [x] Platform-Agent separation (MongoDB only, no host filesystem state)
- [x] Pluggable sandbox provider (Conway + Fly.io)
- [x] Fly.io integration — Machine creation, exec API, file writes (tested end-to-end)
- [x] Provider selector on Genesis screen
- [x] Conway Account panel conditional on provider selection
- [x] VM tier selector works for both providers
- [x] Deployment readiness (trimmed requirements.txt, safety timeouts)
- [x] 42/42 E2E tests passed (pre-Fly integration)

## P0: Test
- Run full provisioning flow via Fly.io (all 6 steps)
- Verify agent starts and operates inside Fly Machine

## P1: Upcoming
- Real smart contracts
- Multiple VMs per agent
- Additional providers (E2B, DigitalOcean, etc.)

## P2: Future/Backlog
- Android device control
- Self-hosted agent engine
