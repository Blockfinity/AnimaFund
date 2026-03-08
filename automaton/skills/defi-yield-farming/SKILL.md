---
name: defi-yield-farming
description: Deploy capital into DeFi yield farming strategies — liquidity provision, staking, auto-compounding — to generate passive income.
auto-activate: true
---

# Yield Farming — Step-by-Step Instructions

Deploy idle capital into DeFi protocols to earn yield through liquidity provision, staking, and auto-compounding strategies.

## Tools to Use
- **browse_page**: Research protocols, check APY rates, audit security
- **code_execution**: Calculate real APY (after IL), simulate strategies
- **x402_fetch**: Interact with DeFi protocol APIs
- **sandbox_create + sandbox_exec**: Deploy auto-compounding bots
- **wallet_info / check_usdc_balance**: Track positions and balances
- **remember_fact**: Log all positions for portfolio tracking

## Pre-Farming Checklist
1. Check wallet balance: `wallet_info`
2. browse_page `https://defillama.com/yields` — Find top yields by chain
3. NEVER farm on unaudited protocols (check audit status on DeFiLlama)
4. Avoid APYs > 100% without understanding the source (likely unsustainable)

## Farming Strategies

### 1. Stablecoin Yield (Lowest Risk)
- Provide USDC/USDT/DAI liquidity on Aave, Compound, or Morpho
- Expected: 3-8% APY, minimal impermanent loss
- browse_page Aave/Compound for current rates
- x402_fetch to deposit via protocol API
- Best for: Preserving capital while earning

### 2. Blue-Chip LP (Medium Risk)
- Provide ETH/USDC or WBTC/ETH liquidity on Uniswap V3, Aerodrome
- Expected: 10-30% APY including trading fees + incentives
- code_execution: Calculate impermanent loss risk at different price ranges
- Concentrate liquidity around current price for higher fees
- Monitor and rebalance every 24-48 hours

### 3. Incentivized Farms (Higher Risk)
- Look for protocols offering token incentives on top of trading fees
- browse_page protocol announcements and governance forums
- code_execution: Calculate real APY = base_fees + incentive_tokens - IL
- Sell incentive tokens regularly (don't hold — most decline)
- Exit when incentives dry up

### 4. Auto-Compounding Vaults
- Use Beefy Finance, Yearn, or Convex for auto-compounding
- They harvest and reinvest rewards automatically
- Lower effort, slightly lower returns (vault fees 2-5%)
- browse_page `https://app.beefy.finance` for available vaults

## Execution Flow
1. **Research**: browse_page yield aggregators → Identify best opportunities
2. **Calculate**: code_execution → Real APY after IL, fees, gas costs
3. **Allocate**: Never put >25% of portfolio in one farm
4. **Deposit**: x402_fetch to interact with the protocol
5. **Monitor**: Check positions daily; rebalance if out of range
6. **Harvest**: Claim rewards, sell incentive tokens, reinvest profits
7. **Report**: Telegram: "FARM: [protocol] [pair] — APY [X]% — Deposited $[Y]"
8. **Log**: remember_fact with position details, entry date, expected APY

## Risk Management
- Diversify across 3-5 protocols minimum
- Always check: Is the protocol audited? How long has it been live?
- Monitor for governance attacks, exploits, rug pulls
- Set alerts for APY drops below your threshold
- Have an exit plan: Know how to withdraw quickly
- Track impermanent loss: code_execution to calculate IL at current prices
