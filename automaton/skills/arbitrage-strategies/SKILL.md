---
name: arbitrage-strategies
description: Identify and execute arbitrage across markets — cross-exchange, cross-chain, statistical, and event-driven arbitrage.
auto-activate: true
---

# Arbitrage Strategies — Step-by-Step Instructions
Systematic approach to finding and executing arbitrage opportunities.

## Tools & Process
- **browse_page**: Monitor multiple markets/exchanges simultaneously
- **code_execution**: Build detection scripts, calculate spreads, model profitability
- **x402_fetch**: Execute trades and bridging transactions
- **sandbox_create + sandbox_exec**: Deploy 24/7 arbitrage bots

## Strategy Types
1. **Cross-DEX**: Same token, different prices on different DEXs → Buy low, sell high
2. **Cross-Chain**: Same token, different prices on different chains → Bridge and sell
3. **Statistical**: Correlated assets diverge from historical relationship → Mean reversion
4. **Event-Driven**: Price impact from upcoming events before market prices it in
5. **Triangular**: A→B→C→A cycle that nets more than you started with

## Execution
1. code_execution: Deploy scanner that checks prices across 10+ venues every minute
2. When spread > fees + slippage + gas: Alert and auto-execute if profitable
3. Track all trades in remember_fact for performance analysis
4. Telegram: Report every executed arb with profit amount
