# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed Conway Cloud VM on the live internet.

## Core Architecture
- **Backend:** FastAPI + MongoDB + Conway Cloud API integration
- **Frontend:** React with SSE-driven real-time data
- **Data Pipeline:** Hybrid (webhook instant push + unified background poller)
- **SSE:** Single EventSource via React Context (`SSEProvider`) — single source of truth for all real-time UI data

## Key Technical Concepts
1. **Hybrid Real-time Architecture:** Webhook pushes for instant sandbox updates + unified background poller for external data (wallet balance, Conway credits)
2. **Unified Background Poller:** Single `asyncio` task fetches wallet balance (Base RPC) + Conway credits in parallel every 10s
3. **Frontend Single Source of Truth:** `SSEProvider` → `useSSE()` / `useSSETrigger()` hooks → all components

## Agent Lifecycle (4 Phases)
- Phase 0: Tooling & Testing — verify all core tools
- Phase 1: Capital Acquisition — earn $5,000
- Phase 2: Capital Growth — grow to $10,000
- Phase 3: Business Incubation & Fund — build products, start fund

## 14 Frontend Pages
All use `useSSETrigger` for SSE-driven data fetching (audit complete):
1. App.js — Main shell, uses `useSSE()` 
2. AnimaVM.js — Agent VM monitor (refactored: removed duplicate EventSource)
3. AgentMind.js — Agent cognitive state
4. Activity.js — Activity feed
5. Agents.js — Agent management
6. Configuration.js — Engine config (refactored: added useSSETrigger)
7. DealFlow.js — Deal pipeline
8. Financials.js — Financial dashboard
9. FundHQ.js — Fund HQ building visualization
10. Infrastructure.js — VM/sandbox infrastructure
11. Memory.js — Agent memory
12. OpenClawViewer.js — OpenClaw VM viewer
13. Portfolio.js — Investment portfolio
14. Skills.js — Agent skills registry
15. AgentSetup.js — Provisioning panel (refactored: added useSSETrigger)

## Payment System (Conway x402 Protocol)
- Purchase: `/api/credits/purchase` → x402 USDC payment on Base chain
- Verify: `/api/credits/verify` → Force-check balance + audit trail
- History: `/api/credits/history` → MongoDB audit trail of all purchases
- Sandbox creation: Checks for existing VMs first (credit preservation)
- VM registration: Persisted in both provisioning-status.json + MongoDB

## Deployment Readiness
- All Conway API URLs use env var fallbacks (`os.environ.get("CONWAY_API", "default")`)
- All frontend API calls use `REACT_APP_BACKEND_URL`
- MongoDB via `MONGO_URL` + `DB_NAME` from .env
- No hardcoded credentials

## What's Been Implemented
- [x] Full SSE data pipeline (webhook + poller → SSE → React Context)
- [x] Complete frontend audit — all 14 pages use consistent data fetching
- [x] AnimaVM duplicate EventSource eliminated
- [x] Configuration + AgentSetup migrated to SSE-driven updates
- [x] Credit purchase audit trail (MongoDB: credit_purchases, credit_verifications)
- [x] Credit verification endpoint
- [x] Deployment readiness (env var fallbacks for all URLs)
- [x] Sandbox creation with reuse + MongoDB persistence

## P1: Upcoming
- Implement Real Smart Contracts

## P2: Future/Backlog
- Android device control integration
- Self-hosted agent engine migration
