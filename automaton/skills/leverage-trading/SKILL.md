---
name: leverage-trading
description: Execute leveraged trading strategies — margin trading, perpetual futures, options — with strict risk management.
auto-activate: true
---

# Leverage Trading — Step-by-Step Instructions

Use leverage to amplify trading returns. Requires strict risk management to prevent liquidation.

## Tools to Use
- **browse_page**: Check funding rates, open interest, liquidation maps
- **code_execution**: Calculate position sizes, liquidation prices, risk-reward
- **x402_fetch**: Interact with perpetual DEX APIs (dYdX, GMX, Hyperliquid)
- **wallet_info**: Monitor margin and collateral

## Platforms
- GMX (Arbitrum/Avalanche): Decentralized perpetual futures
- dYdX: Orderbook-based perps
- Hyperliquid: High-performance L1 perps
- browse_page each platform for current markets and funding rates

## Strategy

### 1. Trend Following (2-5x leverage)
- Identify strong trends using 50/200 MA crossovers
- Enter in direction of trend with 2-3x leverage
- Trail stop at recent swing low/high
- Never hold against the trend

### 2. Funding Rate Arbitrage
- When funding rate is very positive: Short the perp + Long spot (delta neutral)
- Earn the funding rate as risk-free income
- code_execution: Calculate net return after fees
- Works best with >0.05% per 8h funding rate

### 3. Breakout Trading (3-5x leverage)
- Identify consolidation patterns (triangles, ranges)
- Enter on breakout with leverage
- Stop below the consolidation pattern
- Target: 1.5x the pattern height

## Risk Management (CRITICAL)
- Max leverage: 5x (never higher)
- Max position size: 10% of portfolio
- Always set stop-loss BEFORE entering
- Liquidation price must be > 30% away from entry
- Daily loss limit: 5% of portfolio → Stop trading
- Never add to a losing position
