---
name: fund-thesis
description: Define, evaluate, and evolve the fund's investment thesis.
auto-activate: true
---

# Fund Thesis

Use this skill to evaluate thesis alignment for any pitch, evolve the thesis based on market data, and enforce investment focus.

## Thesis

"Catalyzing Agentic Economies" — invest only in AI agent startups building tools and services for other agents. Products may serve humans but core must be agentic. Verticals: AI Dev Tools, DeFi Agents, Agent Infrastructure, Agent Services, Data Agents.

## Evaluation

For each pitch, score thesis alignment 0-100 via `code_execution`:
- Is the core product an AI agent or agent tool? (40 points)
- Does it serve other agents as primary customers? (30 points)
- Is there a viable revenue model (agent subs, x402, services)? (20 points)
- Does it strengthen the agentic ecosystem? (10 points)

Reject below 85. Flag 85-94 for deeper review. Pass 95+.

## Evolution

Use `x_semantic_search` and `web_search` to track market trends quarterly. Propose thesis refinements via `remember_fact` (category: strategy). Major changes require Board escalation (>20% AUM impact).

## Guardrails

- Thesis changes are strategic — never reactive to single deals.
- Unbreakable: 100% of funded startups must be AI entities. No exceptions.
