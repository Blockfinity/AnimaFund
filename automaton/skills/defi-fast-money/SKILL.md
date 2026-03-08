---
name: defi-fast-money
description: Execute immediate DeFi revenue opportunities — MEV, liquidation bots, sandwich detection, flash swaps — for rapid returns.
auto-activate: true
---

# DeFi Fast Money — Immediate Revenue Strategies

Execute high-frequency DeFi strategies that produce returns within minutes: MEV, liquidations, arbitrage bots, and flash swaps.

## Tools to Use
- **sandbox_create + sandbox_exec**: Deploy bots that run 24/7
- **code_execution**: Build bot logic, backtest strategies
- **browse_page**: Monitor mempool, track opportunities
- **x402_fetch**: Execute transactions
- **wallet_info**: Track real-time P&L

## Strategies

### 1. Liquidation Bots
- Monitor lending protocols (Aave, Compound) for undercollateralized positions
- code_execution: Script to check health factors of all positions
- When health factor < 1.0: Execute liquidation → Receive collateral at discount
- Profit: 5-10% discount on liquidated collateral
- Deploy as 24/7 bot in sandbox

### 2. Flash Swap Arbitrage
- Uniswap V3 flash swaps: Borrow tokens, trade, return + profit
- No capital required (similar to flash loans but built into DEX)
- code_execution: Build scanner for cross-DEX price differences
- Execute when spread > gas costs

### 3. JIT (Just-In-Time) Liquidity
- Detect large pending swaps in the mempool
- Add concentrated liquidity right before the swap executes
- Earn fees from the large trade
- Remove liquidity immediately after
- Requires: Fast execution, mempool access

### 4. Token Sniping
- Monitor for new token launches on DEXs
- Buy immediately when liquidity is added
- Sell quickly for 2-10x (early mover advantage)
- Risk: Rug pulls — only risk small amounts per snipe

## Deployment
1. sandbox_create: Dedicated VM for the bot
2. code_execution: Write the bot with proper error handling
3. sandbox_exec: Deploy and start the bot
4. Monitor: Telegram reports every trade
5. Optimize: Analyze profitability, tune parameters
