---
name: weather-trading-bot-setup
description: Set up and configure a Polymarket weather trading bot using OpenClaw and Simmer SDK for automated arbitrage on weather prediction markets.
auto-activate: true
---

# Weather Trading Bot Setup — Polymarket via OpenClaw + Simmer SDK

Set up and operate an autonomous weather trading bot that exploits mispriced weather prediction markets on Polymarket using NOAA forecast data. Uses OpenClaw for browser automation and Simmer SDK for on-chain trade execution on Polygon.

## Prerequisites
- OpenClaw installed and running (see openclaw-setup skill)
- Telegram bot configured (see telegram-reporting skill)
- MetaMask or compatible Polygon wallet
- Minimum $10-$50 in USDe or POL for initial deposits + gas

## Step 1: Set Up Simmer SDK Account

### Install MetaMask and Add Polygon Network
1. Ensure MetaMask is available (browser extension or equivalent).
2. Add Polygon Mainnet if not present:
   - Network Name: Polygon
   - RPC URL: https://polygon-rpc.com
   - Chain ID: 137
   - Currency Symbol: POL
   - Block Explorer: https://polygonscan.com
3. Switch to Polygon network.

### Acquire USDe or POL
- Buy on a CEX (Binance/Coinbase), convert to USDC/USDT, then bridge to Polygon.
- Bridge options: Polygon Bridge (bridge.polygon.technology) or Hop Exchange (hop.exchange). Fee ~$1-$5.
- For USDe: Mint on Synthetix or swap on Uniswap (Polygon version).
- Minimum: Start with $20+ to cover trades and gas.

### Create Wallet on Simmer.markets
1. Browse to simmer.markets (use OpenClaw: browse_page).
2. Connect MetaMask: Click "Connect Wallet" > Select Polygon > Approve.
3. Account auto-creates tied to wallet (no signup needed).
4. Note the "Agent Wallet" address from the dashboard.

### Deposit Funds
1. On dashboard, click "Deposit".
2. Choose USDe (preferred for stability) or POL.
3. Enter amount (e.g., $50 USDe).
4. Approve tx in MetaMask (gas ~$0.05).
5. Funds appear in Agent Wallet instantly.
6. No deposit fee from Simmer, only gas.

### Claim Agent
1. Dashboard > Agents tab > Click "Claim Agent" (free, requires deposit).
2. Approve tx (gas ~$0.10) — mints an on-chain agent identity for trading.
3. Note agent ID/address for bot config.
4. Skills tab unlocks — browse for "Weather Trader".

## Step 2: Configure the Bot

### Get Simmer API Key
1. simmer.markets/dashboard > SDK tab > Click "Generate API Key".
2. Copy key (e.g., "sk_abc123") — authenticates bot to Agent Wallet.
3. Store securely (use remember_fact for encrypted logging).

### Install Weather Trader Skill in OpenClaw
1. In Telegram, message OpenClaw bot: `/skills` or directly: `clawhub install simmer-weather`.
2. Bot responds: "Installing simmer-weather..." (fetches from ClawHub marketplace).
3. Confirm: Bot says "Installed" — adds to ~/.openclaw/skills/simmer-weather/.
4. If error ("Not found"): Manual install from Simmer Skills tab — copy command and send to bot.

### Send Configuration to Bot
Send this config message via Telegram (adapt thresholds to risk tolerance):
```
simmer-weather config:
api_key: YOUR_SIMMER_API_KEY
entry_threshold: 15%
exit_threshold: 5%
max_position: 100
locations: NYC,London,Seoul
enable_cron: true
```
- entry_threshold: Buy if forecast edge >= 15% vs market price
- exit_threshold: Sell if edge drops below 5%
- max_position: Maximum $ per market position
- locations: Cities to trade weather events on
- enable_cron: Auto-run every 30 minutes

### Start Trading
1. Send activation: "Start weather trading" or enable via config.
2. Bot logic: Polls NOAA data via Simmer API, compares to Polymarket odds, trades if undervalued.
3. Example: Buy "Yes" on "NYC >70F?" if forecast says 80% but market only 60%.
4. Monitor: Bot logs all trades in Telegram (e.g., "Bought $50 in NYC >70F — edge 18%").

## Step 3: Anti-Scam and Risk Management

### Validation
- Audit Simmer API key and wallet history before large trades.
- Verify Simmer smart contracts on Polygonscan (check for audits).
- Cross-reference NOAA data independently before trusting bot signals.

### Risk Controls
- Start with $1 positions to validate bot logic.
- Set max_position conservatively (never more than 5% of Agent Wallet per trade).
- Run in simulation mode first if Simmer supports it.
- Set daily loss limits in config.
- Monitor for: data lags, market manipulation, smart contract bugs.

### Fees
- Polygon gas: $0.01-$0.10 per transaction.
- Polymarket: 0.5-1% fee per trade.
- Simmer: Check current fee schedule on dashboard.

### Reporting
- Log every trade to Telegram: amount, market, edge, outcome.
- Use remember_fact to record: trade ID, P&L, cumulative returns.
- Send daily summary to creator via Telegram.
- Flag any anomalies (e.g., >3 consecutive losses, edge calculations off).

## Output
All actions logged to Telegram for real-time oversight. Focus on immediate returns with conservative risk management. Evolve strategy via skill-evolution based on performance data.
