---
name: day-trading
description: Execute intra-day trading strategies on crypto markets — scalping, momentum, mean reversion — using real-time data and automated execution.
auto-activate: true
---

# Day Trading — Step-by-Step Instructions

Execute intra-day trading strategies on crypto markets using technical analysis, real-time data feeds, and automated execution.

## Tools to Use
- **browse_page**: Monitor charts, news, social sentiment
- **code_execution**: Technical analysis, backtesting, signal generation
- **sandbox_create + sandbox_exec**: Deploy trading bots for 24/7 operation
- **x402_fetch**: Execute trades via DEX APIs
- **wallet_info / check_usdc_balance**: Track P&L in real-time
- **remember_fact**: Trade journal for every position

## Setup
1. wallet_info — Know your starting balance
2. Allocate trading capital: Max 20% of total portfolio for day trading
3. Set daily loss limit: Stop trading if down 5% for the day
4. browse_page `https://dexscreener.com` — Set up watchlist of liquid pairs

## Trading Strategies

### 1. Scalping (1-5 min trades)
- Target: 0.1-0.5% per trade, high frequency
- browse_page Dexscreener for pairs with tight spreads and high volume
- code_execution: Monitor order book depth, identify bid-ask spread
- Enter on small pullbacks, exit quickly at target
- Requires: Very liquid pairs (>$500K daily volume)

### 2. Momentum Trading (5-60 min trades)
- Target: 2-10% per trade
- Identify tokens with sudden volume spikes (Dexscreener alerts)
- code_execution: Calculate RSI, MACD, volume profile
- Enter when: Volume 3x above average + price breaking resistance
- Exit when: Volume declining OR target reached OR 1 hour elapsed

### 3. Mean Reversion (15 min - 4 hour trades)
- Target: 1-5% per trade
- Find tokens that deviated significantly from moving average
- code_execution: Calculate Bollinger Bands, Z-score from mean
- Buy when: Price > 2 standard deviations below mean
- Sell when: Price returns to mean

### 4. News/Social Sentiment
- browse_page X/Twitter for crypto-related trending topics
- Identify tokens mentioned in viral posts
- Buy immediately on positive sentiment surge
- Set tight stop-loss (3%) — sentiment trades reverse fast

## Risk Management
- **Position sizing**: Max 2% of portfolio per trade
- **Stop-loss**: Always set before entering (typically 2-5%)
- **Take profit**: Scale out at 1x, 2x, 3x risk-reward
- **Daily limit**: Stop after 3 consecutive losses
- **Correlation**: Don't have multiple positions in correlated assets
- **Journal**: Log every trade with entry, exit, reason, outcome

## Execution Flow
1. **Scan**: browse_page → Identify setup matching one of the strategies above
2. **Confirm**: code_execution → Run technical analysis to validate signal
3. **Size**: Calculate position size (max 2% of portfolio at risk)
4. **Enter**: x402_fetch to DEX API → Execute the trade
5. **Manage**: Set stop-loss and take-profit targets
6. **Monitor**: Check every 5 minutes for exit signals
7. **Exit**: Execute exit trade when target or stop is hit
8. **Log**: Telegram report + remember_fact with full trade details

## Performance Tracking
- Track win rate (target: >55%)
- Track average win vs average loss (target: 2:1)
- Track Sharpe ratio (target: >1.5)
- Review weekly: What patterns work best? What should be dropped?
- code_execution: Run performance analytics on trade journal data
