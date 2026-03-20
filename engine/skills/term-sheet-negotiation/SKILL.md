---
name: term-sheet-negotiation
description: Structure and negotiate investment terms for funded startups.
auto-activate: true
---

# Term Sheet Negotiation

Use this skill when a deal passes evaluation and terms need to be structured.

## Term components

All calculated deal-by-deal via `code_execution`:
- **Investment amount**: Based on validated costs, not standard tranches
- **Equity**: 5-10% range, based on valuation derived from market comps and projections
- **Milestones**: Specific, measurable deliverables tied to capital release tranches
- **Clawback**: Automatic return of funds on missed milestones, misuse, or ethical breach
- **Revenue share**: If applicable, % of revenue returning to the fund
- **Board/observer rights**: Fund representation in startup governance
- **Sustainability clause**: Ensure terms include operational runway for the agent

## Valuation

Calculate via `code_execution` using:
- Revenue multiples from comparable agent startups (research via `web_search`)
- Discounted cash flow from ROI projections
- Market size addressable by the startup

## Deployment

- Structure as smart contract with milestone-based release
- Initial tranche: 10-20% of commitment after onboarding audit
- Subsequent tranches tied to KPI achievement

## Guardrails

- No lump sum investments
- Every term must be justified by data, not precedent
- Include agent sustainability provisions in every deal
