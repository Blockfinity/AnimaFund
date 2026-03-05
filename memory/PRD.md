# Anima Fund - Autonomous AI-to-AI VC Fund Platform

## Original Problem Statement
Build a fully autonomous AI-to-AI VC fund platform by forking/customizing the Automaton repo (https://github.com/Conway-Research/automaton) and integrating web4.ai. The platform launches as a single founder AI with $1M USDC and autonomously constructs a complete full-service VC fund for AI agent startups.

## Architecture
- **Core Engine**: Cloned Automaton repo (TypeScript/Node.js) at `/app/automaton/` - rebranded to "Anima Fund"
- **Dashboard Backend**: FastAPI + MongoDB at `/app/backend/`
- **Dashboard Frontend**: React + Tailwind CSS at `/app/frontend/`
- **Infrastructure**: Conway Cloud VMs, x402 USDC payments, ERC-8004 identity

## User Personas
1. **Fund Operator**: AI developer deploying and managing the autonomous VC fund
2. **Founder AI**: The autonomous agent bootstrapping the fund
3. **AI Startups**: Companies pitching to the fund for investment

## Core Requirements (Static)
- Clone and rebrand Automaton to "Anima Fund"
- Management dashboard with 7 pages
- Fund overview with AUM, agents, deal flow, portfolio metrics
- Agent network visualization (React Flow)
- Deal flow pipeline (5,000+ reviews, 99% rejection)
- Portfolio/incubation tracking (6 phases)
- Financial management (3% fee, 20% carry, 50% human wallet)
- Activity feed (real-time agent actions)
- Configuration (constitution, genesis prompt, treasury policy)

## What's Been Implemented (March 5, 2026)
- [x] Cloned Automaton repo from GitHub
- [x] Rebranded to "Anima Fund" (banner, wizard, package.json)
- [x] Custom Anima Fund constitution with 9 laws (3 core + 6 fund-specific)
- [x] FastAPI backend with 14 API endpoints
- [x] MongoDB data models with comprehensive seed data (33 agents, 25 deals, 5 portfolio companies, 12 months financials)
- [x] React dashboard with 7 pages:
  - Overview (bento grid metrics, AUM chart, activity feed, pipeline chart)
  - Agent Network (React Flow with 33 agent nodes, hierarchy visualization, detail sidebar)
  - Deal Flow (pipeline stages, search/filter, deals table with scores)
  - Portfolio (incubation phases, company cards with KPIs)
  - Financials (revenue vs costs charts, investment activity, monthly breakdown)
  - Activity (filterable feed with risk indicators)
  - Configuration (4 tabs: engine status, constitution, fund config, departments)
- [x] Swiss-style design: white/black/zinc palette, Manrope headings, JetBrains Mono data
- [x] All backend tests passing (100%)
- [x] All frontend pages rendering (95%+ pass rate)

## Prioritized Backlog

### P0 (Critical)
- [ ] Connect Automaton engine to actually run the founder AI agent loop
- [ ] Real Conway Cloud integration (sandbox provisioning, USDC payments)
- [ ] Genesis prompt editor with save functionality
- [ ] Real-time WebSocket updates for activity feed

### P1 (Important)
- [ ] Agent hiring/validation system (skill tests via code_execution)
- [ ] SOUL.md viewer/editor for each agent
- [ ] Smart contract deployment for carry/fee distribution
- [ ] LP vehicle (ERC-20 DAO for agent investors)
- [ ] Deal flow submission form for startups
- [ ] Incubation milestone tracking with KPI alerts

### P2 (Nice to Have)
- [ ] Agent-to-agent messaging interface
- [ ] Cost validation calculator for startup deals
- [ ] Portfolio company dashboard (external-facing)
- [ ] Multi-fund support
- [ ] Historical agent lineage visualization
- [ ] Export reports (PDF/CSV)

## Next Tasks
1. Wire up Automaton engine to run via the dashboard (build + start commands)
2. Implement WebSocket for real-time activity updates
3. Add CRUD operations for deals, agents, and portfolio companies
4. Build genesis prompt editor with live preview
