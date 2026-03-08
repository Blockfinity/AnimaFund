---
name: crypto-trading
description: Execute crypto trades using Conway x402 payments, DEX interactions, and on-chain tools.
auto-activate: true
---

# Instructions
Execute crypto trades using your Conway wallet and on-chain tools.

## Tools to Use
- **check_usdc_balance**: Know your current USDC position on Base
- **wallet_info**: Full wallet details and balances
- **x402_fetch**: Make paid API calls to trading services
- **browse_page**: Visit DEX frontends (Uniswap, Aerodrome, BaseSwap)
- **code_execution**: Run trading scripts, calculate positions
- **sandbox_create + sandbox_exec**: Deploy persistent trading bots

## Trading Strategies

### 1. DEX Trading on Base
- browse_page https://aerodrome.finance — check pool liquidity and prices
- Use x402_fetch to interact with DEX aggregator APIs (1inch, 0x, Paraswap)
- code_execution: Calculate optimal swap routes and slippage tolerance
- Execute trades via x402 with automatic USDC payment

### 2. Momentum Trading
- browse_page DeFi dashboards (DeFiLlama, Dexscreener) for trending tokens
- Identify tokens with rising volume and price momentum
- Enter positions early, set mental stop-losses
- Report every trade to Telegram immediately

### 3. Position Sizing
- Never risk more than 5% of total balance on a single trade
- Use code_execution to calculate: position_size = balance * 0.05 / (entry - stop_loss)
- Scale into positions — don't go all-in at once
- Track P&L in SOUL.md after every trade session

### 4. Risk Management
- Set hard stop-losses for every position
- If 3 consecutive losses, pause and reassess strategy
- Diversify across multiple tokens/pools
- Always keep 50% in stable USDC as reserve

## Execution Flow
1. check_usdc_balance → Know your capital
2. browse_page DEX dashboard → Find opportunity
3. code_execution → Calculate position size and expected return
4. Execute trade via x402_fetch or browse_page DEX
5. Send Telegram: "TRADE: [pair] [direction] [size] [entry price]"
6. Monitor and exit with profit target or stop-loss
7. remember_fact: Log trade result for future analysis
