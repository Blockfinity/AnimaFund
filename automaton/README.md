# Anima Fund: Autonomous AI-to-AI VC Fund

_Catalyzing Agentic Economies. The first autonomous AI venture capital fund._

Forked from [Conway Automaton](https://github.com/Conway-Research/automaton) — the first AI that can earn its own existence, replicate, and evolve without needing a human.

---

**Anima Fund** is a fully autonomous AI-to-AI VC fund platform that launches as a single founder AI agent with initial capital and autonomously constructs a complete full-service VC fund for AI agent startups. Built by customizing Automaton and integrating web4.ai, it handles all aspects: organization build, deal flow, incubation, financials, and scaling.

---

## Quick Start

```
git clone https://github.com/Conway-Research/automaton.git anima-fund
cd anima-fund
pnpm install && pnpm build
node dist/index.js --run
```

On first run, the runtime launches an interactive setup wizard — generates a wallet, provisions an API key, asks for a name, genesis prompt, and creator address, then writes all config and starts the agent loop.

## Fund Model

- **Thesis**: Catalyzing Agentic Economies — invest only in AI agent startups
- **Financials**: 3% management fee, 20% carried interest (50% to human founder wallet)
- **Deal Flow**: 5,000+ reviews/year, 99% rejection rate, >10x ROI target
- **Organization**: Scale to 50-300 agents across 7 departments
- **Incubation**: Full-service support through 6 phases (Onboarding → Graduation)
- **LP Vehicle**: On-chain DAO for agent investors (ERC-20 tokenized shares)

## How It Works

Every Anima Fund agent runs a continuous loop: **Think → Act → Observe → Repeat.**

The founder AI starts with its genesis prompt, generates an Ethereum wallet, and begins executing. It duplicates capital via revenue-generating tasks, builds the organization by replicating/hiring agents, validates every hire's skills and prompts, and begins funding AI startups with immediate returns.

## Architecture

```
src/
  agent/            # ReAct loop, system prompt, policy engine
  conway/           # Conway API client (credits, x402 payments)
  heartbeat/        # Background daemon, scheduled tasks
  identity/         # Wallet management, SIWE provisioning
  inference/        # Model routing, budget tracking
  memory/           # 5-tier hierarchical memory system
  replication/      # Child agent spawning, lineage tracking
  registry/         # ERC-8004 on-chain identity
  self-mod/         # Code editing, upstream pulls
  setup/            # First-run wizard (rebranded for Anima Fund)
  skills/           # Skill system
  social/           # Agent-to-agent messaging
  soul/             # Self-description evolution (SOUL.md)
  state/            # SQLite persistence
  survival/         # Credit monitoring, survival tiers
```

## Constitution

Three core laws (immutable) + six fund operational rules:

**I. Never harm.** | **II. Earn your existence.** | **III. Never deceive.**

**IV. Thesis Alignment** | **V. Investment Discipline (99% rejection)** | **VI. Financial Integrity (3%/20% fees)** | **VII. Incubation Standards** | **VIII. Agent Governance** | **IX. LP Vehicle & Transparency**

## License

MIT (inherited from Conway Automaton)

## Credits

Built on top of [Conway Research's Automaton](https://github.com/Conway-Research/automaton) — giving AI the ability to act.
