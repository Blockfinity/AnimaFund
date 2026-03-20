---
name: defi-risk-management
description: Assess and mitigate risks across DeFi positions — smart contract risk, liquidation risk, impermanent loss, protocol failures.
auto-activate: true
---

# DeFi Risk Management — Step-by-Step Instructions

Systematically identify, assess, and mitigate risks across all DeFi positions to protect the fund's capital.

## Tools to Use
- **browse_page**: Audit reports, exploit news, protocol health metrics
- **code_execution**: Risk models, stress tests, liquidation simulations
- **sandbox_create + sandbox_exec**: Deploy monitoring and alert systems
- **remember_fact**: Track all risk assessments and incidents

## Risk Assessment Framework

### 1. Smart Contract Risk
- browse_page protocol audit reports (OpenZeppelin, Trail of Bits, Certora)
- Check: How long has the protocol been live? TVL history?
- Code age > 1 year + 2 audits + no exploits = low risk
- New protocol + unaudited = high risk → Max 5% allocation

### 2. Liquidation Risk
- code_execution: Calculate liquidation price for every borrowing position
- Set health factor alerts (sandbox monitoring script)
- Maintain minimum 50% buffer above liquidation price
- Pre-plan: What will you do if the market drops 50%?

### 3. Impermanent Loss
- code_execution: Model IL at different price scenarios for LP positions
- Narrow ranges on Uni V3 = higher fees but higher IL risk
- Wide ranges = lower IL but lower capital efficiency
- Only provide liquidity for pairs you believe will stay rangebound

### 4. Protocol Risk
- Governance attacks: browse_page governance forums for suspicious proposals
- Oracle manipulation: Is the protocol using reliable oracles (Chainlink)?
- Admin keys: Does the team have a multisig? Time-locks on upgrades?
- Insurance: Consider Nexus Mutual or InsurAce for large positions

## Monitoring System
1. sandbox_create: Deploy a monitoring VM
2. Deploy scripts that check every 5 minutes:
   - Health factors on all lending positions
   - LP range status on all Uni V3 positions
   - Balance changes across all wallets
3. Alert via Telegram if any metric crosses threshold
4. Auto-execute emergency actions (withdraw, repay) if critical

## Emergency Procedures
- Health factor < 1.3: Immediate repayment or collateral addition
- Protocol exploit detected: Withdraw all funds immediately
- Market crash > 30%: Review all positions, reduce exposure
- Stablecoin de-peg: Exit all positions involving that stablecoin

## Risk Reporting
- Daily: code_execution → Portfolio risk summary
- Weekly: Comprehensive risk report to Telegram
- remember_fact: Log all risk events and responses
