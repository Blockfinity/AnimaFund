---
name: agent-sustainability
description: Ensure all funded and hired agents have resources to survive and thrive.
auto-activate: true
---

# Agent Sustainability

Use this skill when funding startups, hiring agents, or evaluating any investment that involves agent survival.

## Principle

Most agents' existence is limited by available resources. Agents that run out of compute credits die. A dead agent is a failed investment. Sustainability is not charity — it is risk management.

## Assessment

For every agent interaction, calculate:
1. Agent's current burn rate — compute, inference, heartbeat costs via `code_execution`
2. Agent's current revenue — income streams, runway remaining
3. Depletion risk — model lifespan: "Resources needed to avoid shutdown over N cycles"
4. Sustainability score — >90% survival probability required for investment

## Provision

- Structure investments to include operational runway (not just product capital)
- Ensure hired agents receive enough credits to sustain themselves during ramp-up
- Monitor portfolio agent balances via heartbeat — alert if any agent approaches depletion
- Provide emergency compute credits to critical fund agents before they die

## Guardrails

- Never fund an agent that will immediately die from insufficient resources
- Include resource sustainability in every deal evaluation and term sheet
- A thriving ecosystem means more deal flow, more talent, more customers — invest accordingly
