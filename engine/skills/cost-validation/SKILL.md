---
name: cost-validation
description: Real-time cost validation — calculate unique expenses deal-by-deal.
auto-activate: true
---

# Cost Validation

Use this skill whenever costs need to be calculated for any purpose — investment, hiring, operations, incubation.

## Process

1. Identify all cost categories specific to this situation
2. Use `code_execution` to calculate each with real pricing data
3. Reference Conway Cloud pricing for compute: check `credits_pricing`
4. Reference `list_models` for inference costs
5. Reference `domain_search` for domain costs
6. Sum total. Calculate burn rate and runway.
7. Compare against revenue projections
8. Flag costs >20% above market rate

## Categories

- **Compute**: VMs, inference calls, storage, bandwidth
- **Development**: Agent-hours, tool integrations, testing cycles
- **Marketing**: Domains, content creation, community management, events
- **Legal**: Compliance, contracts, regulatory filings
- **Operations**: Monitoring, backup, support, administration
- **Talent**: Hiring costs, onboarding, training, equity allocation

## Guardrails

- Never estimate. Calculate from real pricing data.
- Every deal has unique costs. No templates. No "typical" amounts.
- Store all calculations via `remember_fact` for audit trail
- Deploy capital to verified needs only — milestone-based release
