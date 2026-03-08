---
name: defi-dex-trading
description: Trade tokens on decentralized exchanges (DEXs) using real-time price data, slippage analysis, and on-chain execution via Conway tools.
auto-activate: true
---

# DEX Trading — Step-by-Step Instructions

Trade crypto tokens on decentralized exchanges using real-time market data, technical analysis, and on-chain execution.

## Tools to Use
- **browse_page**: Monitor DEX dashboards, token prices, trending pairs
- **x402_fetch**: Call DEX APIs for real-time quotes and execute swaps
- **code_execution**: Calculate slippage, analyze charts, build trading scripts
- **sandbox_create + sandbox_exec**: Deploy persistent trading bots
- **wallet_info / check_usdc_balance**: Track wallet balances
- **remember_fact**: Log all trades for performance tracking

## Pre-Trade Setup
1. Check your wallet balance: `wallet_info` or `check_usdc_balance`
2. Browse trending pairs: `browse_page https://dexscreener.com/base` for Base chain
3. Identify high-volume, liquid pairs (min $100K daily volume)
4. Set risk limits: Never risk more than 5% of portfolio on a single trade

## Trading Strategy

### 1. Momentum Trading
- browse_page Dexscreener for tokens with >20% gain in 1h AND rising volume
- code_execution: Calculate RSI, moving averages from price history
- Entry: Buy when price pulls back to 20-period MA after breakout
- Exit: Sell at 2x risk-reward ratio or when volume declines

### 2. Range Trading
- Identify tokens trading in a defined range (support/resistance)
- code_execution: Plot support/resistance from recent price data
- Buy near support, sell near resistance
- Stop loss: 3% below support

### 3. News/Event Trading
- browse_page crypto news sites (CoinDesk, The Block, CT on X)
- Identify catalysts: token launches, partnerships, listings
- Enter BEFORE the event if possible, exit on the news
- Use discover_agents to get intel from other trading agents

## Execution Flow
1. **Scan**: browse_page DEX dashboards → Identify opportunity
2. **Analyze**: code_execution → Price analysis, slippage calculation
3. **Size**: Calculate position size (max 5% of portfolio)
4. **Execute**: x402_fetch to DEX API or use sandbox to run swap script
5. **Monitor**: Set take-profit and stop-loss levels
6. **Report**: Telegram: "TRADE: [BUY/SELL] [token] at $[price] — [reason]"
7. **Log**: remember_fact with entry price, size, rationale

## Risk Management
- Never trade illiquid pairs (< $50K daily volume)
- Always calculate gas costs BEFORE trading (must be < 1% of trade size)
- Maximum 3 concurrent positions
- Daily loss limit: 10% of portfolio → Stop trading for the day
- Always have a stop-loss plan before entering

## DEX Resources
- Base chain: Aerodrome, BaseSwap, Uniswap V3
- Solana: Jupiter, Raydium, Orca
- Price feeds: Dexscreener, DeFiLlama, CoinGecko API
