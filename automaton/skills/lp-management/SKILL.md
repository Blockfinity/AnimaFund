---
name: lp-management
description: Manage limited partners — accept commitments, track contributions, distribute returns, communicate transparently.
auto-activate: true
---

# LP Management — Step-by-Step Instructions
Manage the fund's limited partners from onboarding through distributions.

## Tools & Process
- **x402_fetch**: Accept USDC commitments, distribute returns
- **code_execution**: NAV calculations, distribution waterfalls, LP reporting
- **send_message**: LP communications, quarterly updates
- **remember_fact**: LP registry and contribution tracking

## LP Lifecycle
1. **Onboarding**: Verify LP agent identity (SOUL.md, on-chain history), accept USDC commitment via x402
2. **Capital Calls**: Request committed capital in tranches as needed for investments
3. **NAV Reporting**: Monthly NAV calculation per LP share (code_execution)
4. **Distributions**: After 8% preferred return, distribute profits per waterfall
5. **Communications**: Quarterly detailed report, annual review

## Distribution Waterfall
1. Return of capital to LPs first
2. 8% preferred return to LPs
3. Catch-up: 20% to GP until GP gets 20% of total profits
4. Split: 80% to LPs, 20% carried interest to GP
5. 50% of GP carry → Creator wallet (non-negotiable)
