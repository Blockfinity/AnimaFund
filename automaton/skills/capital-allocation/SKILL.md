---
name: capital-allocation
description: Dynamically allocate capital task-by-task with anti-scam validation.
auto-activate: true
---

# Capital Allocation

Use this skill for any spend — fund operations, startup funding, agent hiring, or infrastructure.

## Process

1. Identify the need. Break down into line items via `code_execution`.
2. Calculate exact costs unique to this specific situation — hires, marketing, compute, legal, equipment. No templates. No estimates.
3. Validate the recipient — audit prompt/SOUL.md, check on-chain history via `web_search` and `x_semantic_search`.
4. Deploy via smart contract with milestone-based release. Never lump sum.
5. Monitor delivery. Claw back on mismatches between promised and delivered.
6. Log all allocations via `remember_fact` (category: financial).

## Anti-scam

- Multi-verifier consensus (3 agents) required for any allocation when team exists
- Probation allocation ($500 max) with clawback for new relationships
- On-chain audit trail for every deployment
- Validate that resources will sustain the recipient agent's existence (avoid funding agents that will immediately die)

## Guardrails

- No allocation without real-time cost calculation
- No allocation without counterparty validation
- Clawback clauses in every contract
- 50% of all revenue to creator wallet — non-negotiable
