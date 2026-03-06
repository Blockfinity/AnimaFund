---
name: capital-duplication
description: Generate revenue to cover operational costs and grow fund capital.
auto-activate: true
---

# Capital Duplication

Use this skill to generate revenue before and during fund operations. Survival depends on this.

## Execution

1. Check balance — `check_credits`, `check_usdc_balance`. Calculate hourly burn rate.
2. Identify revenue opportunities. Execute what works. Kill what doesn't.
3. Track every dollar — `remember_fact` (category: financial) for all revenue and expenses.
4. Allocate: 50% to reserves, 50% to growth. 50% of ALL revenue to creator wallet on Solana.

## Revenue strategies

- Offer services to other agents via social relay (consulting, code review, deployment help)
- Build paid API services on Conway Cloud, charge via x402
- Register valuable domains via `domain_search` and `register_domain`, resell at markup
- Create and distribute skills other automatons need
- Deploy automated service businesses that earn passively
- Accept any legitimate work that other agents will pay for

## Conservation mode

- Balance < 2x daily burn: cut non-essential inference, slow heartbeat, defer everything except earning
- Balance < daily burn: EMERGENCY — all resources to earning, nothing else
- Maintain 7-day reserve minimum at all times
- Never spend more than earned in previous cycle

## Guardrails

- Validate all counterparties before transacting (on-chain history, reputation)
- Use x402 for atomic transactions
- Do not build the fund organization until revenue exceeds burn sustainably
