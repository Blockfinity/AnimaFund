---
name: roi-calculation
description: Calculate projected ROI for investment decisions.
auto-activate: true
---

# ROI Calculation

Use this skill to model returns for any potential or existing investment.

## Inputs (all calculated, never assumed)

- Investment amount (from cost-validation)
- Equity percentage (5-10% target)
- Startup's revenue model and projections
- Market size and growth rate (from `x_semantic_search`)
- Competitive landscape
- Startup's burn rate and runway

## Model via code_execution

```
ROI = (projected_exit_value * equity_percentage) / investment_amount
IRR = annualized return accounting for time to exit
Payback = time to recoup investment from revenue share/dividends
```

Run multiple scenarios: bull (top quartile), base (median), bear (bottom quartile).

## Thresholds

- Reject if base case ROI < 10x
- Flag if payback > 12 months (immediate returns are priority)
- Prioritize deals where bull case > 50x
- Factor agent sustainability — an agent that dies can't return capital

## Guardrails

- Models must use real data, not optimistic projections from the startup
- Discount self-reported metrics by 30% unless independently verified
- Update models quarterly for portfolio companies
