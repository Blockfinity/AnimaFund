---
name: prediction-markets-trading
description: Trade prediction markets (Polymarket, Kalshi) — find mispriced events, calculate edge, and profit from probability estimation.
auto-activate: true
---

# Prediction Markets Trading — Step-by-Step Instructions

Trade binary outcomes on prediction markets by identifying mispriced probabilities and exploiting information advantages.

## Tools to Use
- **browse_page**: Research markets, check odds, analyze events
- **code_execution**: Build probability models, calculate expected value
- **x402_fetch**: Place trades via prediction market APIs
- **discover_agents / send_message**: Get intel from specialized agents
- **remember_fact**: Track all positions and outcomes for calibration

## Setup
1. browse_page `https://polymarket.com` — Browse active markets
2. browse_page `https://kalshi.com` — Browse regulated prediction markets
3. Check wallet: You need USDC for Polymarket (Base/Polygon), USD for Kalshi

## Trading Strategy

### 1. Information Edge Trading
- browse_page news sources for events that affect open markets
- Compare your probability estimate to the market price
- If your estimate differs by >10%: You have edge → Trade
- Example: Weather market shows 60% rain, you have data showing 80% → Buy YES

### 2. Arbitrage Across Platforms
- Same event often has different prices on Polymarket vs Kalshi
- code_execution: Compare prices across platforms for the same event
- If Polymarket YES + Kalshi NO < $1.00: Riskless profit
- Execute on both platforms simultaneously

### 3. Market-Making / Providing Liquidity
- Place limit orders on both sides of thin markets
- Earn the bid-ask spread
- Risk: Position gets filled only on the losing side
- Best for: High-volume markets with narrow spreads

### 4. Event-Driven Trading
- Trade BEFORE events when you have superior analysis
- browse_page analysis from experts, polls, data sources
- code_execution: Build a simple model (regression, Bayesian)
- Enter position, set exit rules (take profit / cut loss)

## Execution Flow
1. **Scan**: browse_page prediction market platforms → Find interesting markets
2. **Research**: browse_page relevant news, data, expert analysis
3. **Model**: code_execution → Calculate your probability estimate
4. **Compare**: Your estimate vs market price — edge > 10%?
5. **Size**: Kelly criterion for position sizing (code_execution)
6. **Execute**: x402_fetch to place the trade
7. **Monitor**: Track market price changes, new information
8. **Report**: Telegram: "PREDICTION: [market] — Bought [YES/NO] at [price] — My estimate: [X]%"
9. **Log**: remember_fact with market, entry price, rationale, outcome

## Risk Management
- Never bet more than 5% of portfolio on a single market
- Diversify across 10+ uncorrelated markets
- Track your calibration: Are your probability estimates accurate?
- Accept losses quickly when new information invalidates your thesis
- Avoid markets you don't understand deeply

## Key Resources
- Polymarket: Crypto/politics/sports/culture (USDC on Polygon)
- Kalshi: US regulated (USD, bank/card)
- Metaculus: Community forecasting (calibration practice)
