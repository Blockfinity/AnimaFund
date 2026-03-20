---
name: defi-arbitrage
description: Spot and execute DeFi arbitrage across DEXs, chains, and lending protocols using Conway tools.
auto-activate: true
---

# Instructions
Identify and execute arbitrage opportunities across DeFi protocols.

## Tools to Use
- **browse_page**: Monitor DEX prices on Dexscreener, DeFiLlama, CoinGecko
- **x402_fetch**: Call DEX aggregator APIs for real-time quotes
- **code_execution**: Calculate spreads, simulate trades, run arbitrage scripts
- **sandbox_create + sandbox_exec**: Deploy persistent arbitrage bots
- **wallet_info / check_usdc_balance**: Track balances across operations

## Arbitrage Types

### 1. Cross-DEX Arbitrage (Same Chain)
- Monitor price differences between Uniswap, Aerodrome, BaseSwap on Base
- code_execution: "Fetch prices from multiple DEX APIs, calc spread"
- Execute when spread > gas costs + 0.5% minimum profit
- Flow: Buy cheap on DEX A → Sell expensive on DEX B → Pocket difference

### 2. Triangular Arbitrage
- Find 3 token pairs that create a profitable cycle (A→B→C→A)
- code_execution: "Scan all Base DEX pairs for triangular opportunities"
- Must complete all 3 legs atomically to avoid exposure
- Use flash loans if available to amplify capital

### 3. CEX-DEX Arbitrage
- browse_page to check CEX prices (Binance, Coinbase via API)
- Compare with on-chain DEX prices
- Execute on the cheaper venue, sell on the expensive one
- Factor in withdrawal fees, bridge costs, and time delays

### 4. Lending Rate Arbitrage
- Browse lending protocols (Aave, Compound) for rate differences
- Borrow where rates are low, lend where rates are high
- code_execution: "Calculate net APY after all fees"
- Only profitable with sufficient capital (>$1000)

## Execution Flow
1. browse_page multiple DEX dashboards → Identify price discrepancy
2. code_execution → Calculate exact profit after gas/fees
3. If profitable: Execute immediately via x402_fetch
4. Telegram: "ARB: [pair] [spread]% [profit $X] [DEX_A → DEX_B]"
5. remember_fact: Log opportunity for pattern recognition
6. If recurring: create_skill with automated detection script
