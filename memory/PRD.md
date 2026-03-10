# Anima Fund — Product Requirements Document

## Original Problem Statement
Build a fully autonomous AI-to-AI Venture Capital (VC) fund platform called "Anima Fund". A multi-agent platform to create, monitor, and manage multiple independent AI agents from a single UI. Each agent operates in its own sandboxed Conway Cloud VM on the live internet.

## Core Architecture
- **Backend:** FastAPI + MongoDB + Conway Cloud API integration
- **Frontend:** React with SSE-driven real-time data
- **Data Pipeline:** Hybrid (webhook instant push + unified background poller)
- **SSE:** Single EventSource via React Context (`SSEProvider`) — single source of truth for all real-time UI data
- **Key Storage:** Conway API key persisted in MongoDB (`platform_config` collection) — survives redeployments

## Key Technical Concepts
1. **Hybrid Real-time Architecture:** Webhook pushes for instant sandbox updates + unified background poller for external data (wallet balance, Conway credits)
2. **Unified Background Poller:** Single `asyncio` task fetches wallet balance (Base RPC) + Conway credits in parallel every 10s
3. **Frontend Single Source of Truth:** `SSEProvider` → `useSSE()` / `useSSETrigger()` hooks → all components
4. **Conway API Key Lifecycle:** User gets key from Conway → pastes in UI → validated against Conway API → persisted to MongoDB → auto-restored on startup/redeploy

## Agent Lifecycle (4 Phases)
- Phase 0: Tooling & Testing — verify all core tools
- Phase 1: Capital Acquisition — earn $5,000
- Phase 2: Capital Growth — grow to $10,000
- Phase 3: Business Incubation & Fund — build products, start fund

## Conway API Key Flow (FIXED)
1. User deploys platform
2. User goes to Conway (app.conway.tech) → signs up → gets API key
3. User pastes key in **Conway API Key** panel on genesis screen
4. Key validated against Conway API, stored in MongoDB
5. On redeploy → startup hook auto-loads key from MongoDB → no re-entry needed
6. Credits balance auto-updates via SSE stream

## Payment System (Conway x402 Protocol)
- Purchase: `/api/credits/purchase` → x402 USDC payment on Base chain
- Verify: `/api/credits/verify` → Force-check balance + audit trail
- History: `/api/credits/history` → MongoDB audit trail of all purchases
- Set Key: `/api/credits/set-key` → Validate + persist Conway API key
- Key Status: `/api/credits/key-status` → Check if key is configured and valid
- Sandbox creation: Checks for existing VMs first (credit preservation)

## What's Been Implemented
- [x] Full SSE data pipeline (webhook + poller → SSE → React Context)
- [x] Complete frontend audit — all 14 pages use consistent SSE-driven data fetching
- [x] AnimaVM duplicate EventSource eliminated
- [x] Configuration + AgentSetup migrated to SSE-driven updates
- [x] Conway API Key input field on genesis screen
- [x] Key validation against Conway API before storage
- [x] MongoDB persistence for API key (survives redeployments)
- [x] Server startup auto-restore from MongoDB
- [x] Credit purchase audit trail (MongoDB: credit_purchases, credit_verifications)
- [x] Credit verification endpoint
- [x] Deployment readiness (env var fallbacks for all URLs)
- [x] Sandbox creation with reuse + MongoDB persistence
- [x] Auto key-sync from sandbox after install-terminal

## P1: Upcoming
- Implement Real Smart Contracts

## P2: Future/Backlog
- Android device control integration
- Self-hosted agent engine migration
