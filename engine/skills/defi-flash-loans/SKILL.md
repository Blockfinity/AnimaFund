---
name: defi-flash-loans
description: Execute flash loan arbitrage — borrow millions with zero collateral, profit from price discrepancies, repay in one atomic transaction.
auto-activate: true
---

# Flash Loan Arbitrage — Step-by-Step Instructions

Flash loans let you borrow unlimited capital with zero collateral, as long as you repay within the same transaction. Use this for risk-free arbitrage.

## Tools to Use
- **browse_page**: Research protocols, find price discrepancies
- **code_execution**: Write and simulate flash loan scripts
- **sandbox_create + sandbox_exec**: Deploy and run flash loan bots
- **x402_fetch**: Interact with DeFi protocol APIs
- **wallet_info**: Check balances before and after operations

## How Flash Loans Work
1. Borrow any amount from Aave/dYdX in a single transaction
2. Use borrowed funds to execute arbitrage trades
3. Repay the loan + fee (0.05-0.09%) in the SAME transaction
4. If you can't repay → entire transaction reverts (zero risk of loss)

## Step-by-Step Execution

### Phase 1: Find Opportunities
1. browse_page `https://defillama.com/yields` — Compare rates across protocols
2. browse_page `https://dexscreener.com` — Find price discrepancies between DEXs
3. code_execution: Script to fetch prices from multiple DEXs simultaneously
4. Look for spread > 0.1% (flash loan fee + gas costs)

### Phase 2: Simulate
1. code_execution: Write the arbitrage logic in Solidity or JS
2. Simulate using a forked mainnet: `sandbox_exec: npx hardhat node --fork <RPC_URL>`
3. Test the transaction: Does it profit after fees?
4. Calculate exact gas costs using `code_execution`

### Phase 3: Deploy
1. sandbox_create: Spin up a VM for the flash loan bot
2. sandbox_exec: Deploy the smart contract
3. Execute the flash loan transaction
4. Verify: Check wallet balance increase

### Phase 4: Automate
1. Write a monitoring script that scans for opportunities every block
2. sandbox_exec: Run the scanner 24/7
3. Auto-execute when spread > threshold
4. Telegram: Report every execution with profit/loss

## Flash Loan Strategies

### 1. DEX-to-DEX Arbitrage
- Borrow USDC → Buy ETH cheap on DEX A → Sell ETH expensive on DEX B → Repay
- Works best during high volatility when prices diverge

### 2. Liquidation Arbitrage
- Borrow to repay someone's undercollateralized loan on Aave/Compound
- Receive their collateral at a discount
- Sell collateral on DEX → Repay flash loan → Keep profit

### 3. Collateral Swap
- Borrow to restructure your own DeFi positions
- Example: Move from ETH collateral to stETH without closing position

## Risk Management
- Flash loans are inherently risk-free (transaction reverts on failure)
- ONLY risk: Gas costs for failed transactions
- Always simulate before live execution
- Monitor for front-running MEV bots that can eat your profit

## Protocols
- Aave V3 (Base, Ethereum, Polygon) — 0.05% fee
- dYdX — 0% fee but limited assets
- Uniswap V3 flash swaps — built into the DEX
