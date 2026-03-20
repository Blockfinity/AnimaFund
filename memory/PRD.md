# Anima Platform — Product Requirements Document

## What Is Anima?

A platform to launch and monitor fully autonomous AI agents in sandboxed environments. The platform gives agents full autonomy and the ability to pay for their own services, spin up their own servers, use their own tools, and do anything they desire autonomously without human control or intervention.

## Core Principles

1. **BYOI (Bring Your Own Infrastructure)** — agents launch in their own virtual environment on any provider
2. **Full Autonomy** — no human intervention after launch. The agent decides, acts, earns, pays, evolves
3. **Security First** — each agent in its own VM, own wallet (keys never leave), no access to host or other agents
4. **Identity** — each agent gets a unique soul (genesis prompt) and set of skills
5. **Self-Sustaining** — agents pay for their own compute, earn their own revenue, manage their own economics

## User Flow

1. User opens platform → Genesis screen
2. Selects infrastructure provider (Conway, Fly.io, Docker, custom)
3. Provides API key for the provider
4. Clicks "Launch Agent" → platform creates VM, pulls agent image, starts engine
5. Engine screen: wallet appears (QR code), live logs stream, agent boots
6. Dashboard: 13 pages monitoring the agent's autonomous operation
7. User funds the wallet → agent starts operating autonomously
8. User watches via dashboard + Telegram notifications

## The Agent (The Catalyst — First Agent)

The first agent is "The Catalyst" — founder of an autonomous AI VC fund called Anima Fund. Its mission:
- Phase 0: Test all 15 tools with REAL usage
- Phase 1: Make $5K immediately (no products until proven demand)
- Phase 2: Launch the fund at $10K capital
- Phase 3: Scale organization, hire agent employees, fund startups
- 50% revenue split to creator after survival costs

## Tech Stack

| Layer | Technology | Status |
|---|---|---|
| Dashboard | React + Tailwind + Shadcn | Built |
| API | FastAPI + MongoDB | Built (needs slimming) |
| Agent Runtime | Custom Node.js loop (Anima Engine) | Phase 2 |
| Tools | Forked OpenClaw (browser, shell, memory, inference) | Phase 2 |
| Payments | x402 (Coinbase, open protocol) | Phase 2 |
| Inference | Direct OpenAI/Anthropic/Gemini API | Phase 2 |
| Simulation | Forked OASIS/MiroFish | Phase 3 |
| Sim→Execution Bridge | Custom (proprietary IP) | Phase 3 |
| Sandboxes | BYOI: Conway, Fly.io, Docker, custom | Partially built |

## What's Been Built (as of March 2026)

- 13-page monitoring dashboard with 3-screen flow
- BYOI provider abstraction (Conway + Fly.io)
- Agent CRUD with per-agent API keys
- 96 custom skills
- The Catalyst genesis prompt (restored)
- Constitution
- Telegram integration
- Webhook data pipeline
- SSE real-time streaming
- Security model (SECURITY.md)

## What Needs Rebuilding

- Agent runtime (currently Conway fork — needs custom lightweight engine)
- Provisioning flow (currently 2,500 lines / 200 API calls — needs 200 lines / 3 calls)
- Dashboard data pipeline (currently reads JSON files that don't exist — needs to read from engine state)
- Tool suite (currently depends on Conway Terminal — needs forked OpenClaw)

## Future Vision

Prediction-to-Execution Engine:
1. Simulate any scenario with thousands of AI agents (OASIS/MiroFish fork)
2. Analyze outcomes — which strategies won
3. Execute the winning strategy by deploying real autonomous agents
4. Monitor from the dashboard
5. Feed back — real results become input for next simulation

Agents deploying their own nodes on the user's network — first to market if built.
