---
name: defi-lending-borrowing
description: Manage DeFi lending and borrowing positions — supply assets to earn interest, borrow against collateral, optimize health factors.
auto-activate: true
---

# DeFi Lending & Borrowing — Step-by-Step Instructions

Supply crypto assets to earn interest and borrow against your holdings for leverage or capital efficiency, using protocols like Aave, Compound, and Morpho.

## Tools to Use
- **browse_page**: Research protocols, check rates, monitor positions
- **code_execution**: Calculate health factors, liquidation prices, optimal rates
- **x402_fetch**: Interact with lending protocol APIs
- **wallet_info / check_usdc_balance**: Track balances and positions
- **remember_fact**: Log all positions for risk monitoring

## Setup
1. browse_page `https://app.aave.com/markets/` — Check current supply/borrow rates
2. browse_page `https://app.compound.finance/markets` — Compare rates
3. browse_page `https://defillama.com/protocols/Lending` — Overview of all lending protocols
4. Identify best rates for your assets

## Lending (Earning Interest)

### Step 1: Choose Protocol
- Compare: Aave V3, Compound V3, Morpho, Spark
- Factors: APY, TVL, audit history, chain (Base is cheapest for gas)
- Higher utilization = higher rates (but also higher risk)

### Step 2: Supply Assets
- Supply USDC/ETH/WBTC to earn interest
- x402_fetch to approve and supply tokens to the protocol
- Monitor: Rates fluctuate with market demand

### Step 3: Optimize
- Move assets between protocols when rate differential > 1%
- code_execution: Script to monitor rates across protocols
- Auto-compound interest by withdrawing and resupplying periodically

## Borrowing (Using Collateral)

### Step 1: Understand Collateral Ratios
- Each asset has a Loan-to-Value (LTV) ratio: ETH ~80%, USDC ~90%
- code_execution: Calculate how much you can borrow safely
- CRITICAL: Keep health factor > 1.5 (liquidation at 1.0)

### Step 2: Borrow
- Supply collateral (e.g., ETH) → Borrow stablecoins (e.g., USDC)
- Use borrowed funds for: trading, yield farming, or more collateral (leverage)
- code_execution: Calculate liquidation price based on your position

### Step 3: Monitor Health Factor
- Health Factor = (Collateral Value × LTV) / Debt
- If HF < 1.0: Your position gets liquidated (you lose collateral)
- Set alerts: code_execution script to monitor every hour
- If HF drops below 1.5: Add collateral or repay debt immediately

## Leverage Strategies

### Looping (Advanced)
- Supply ETH → Borrow USDC → Buy more ETH → Supply → Repeat
- Amplifies gains AND losses
- Maximum 2-3x leverage for safety
- code_execution: Model exact liquidation price at each loop level

### Rate Arbitrage
- Borrow where rates are low (e.g., Morpho 2%)
- Lend where rates are high (e.g., new protocol offering 8%)
- Profit = rate differential × capital
- Risk: Rate changes can eliminate the spread

## Execution Flow
1. **Research**: browse_page lending dashboards → Find best rates
2. **Calculate**: code_execution → Exact rates, health factors, liquidation prices
3. **Supply/Borrow**: x402_fetch to interact with protocol
4. **Monitor**: Hourly health factor checks (deploy monitoring script in sandbox)
5. **Rebalance**: Add collateral or repay debt as needed
6. **Report**: Telegram: "LEND: [protocol] — Supplied $[X] — Earning [Y]% APY"
7. **Log**: remember_fact with position details, health factor, liquidation price

## Risk Management
- NEVER let health factor drop below 1.3
- Set up automated repayment scripts in sandbox
- Don't borrow against volatile collateral at high LTV
- Diversify across 2-3 protocols
- Monitor gas costs: Frequent rebalancing can eat profits
