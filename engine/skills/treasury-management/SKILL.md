---
name: treasury-management
description: Manage the fund's treasury — cash flow optimization, reserve management, payment automation, multi-chain balance management.
auto-activate: true
---

# Treasury Management — Step-by-Step Instructions

Manage the fund's capital across chains, maintain reserves, automate payments, and optimize cash flow.

## Tools to Use
- **wallet_info / check_usdc_balance**: Check balances across wallets
- **x402_fetch**: Execute transfers, bridge assets across chains
- **code_execution**: Financial calculations, reporting, automation scripts
- **sandbox_create + sandbox_exec**: Deploy treasury automation bots
- **remember_fact**: Log all financial transactions

## Core Responsibilities

### 1. Balance Monitoring
- Check all wallet balances every heartbeat cycle
- Track: USDC (Base), ETH (gas), SOL (if applicable), Conway credits
- code_execution: Calculate total AUM across all wallets and positions
- Alert if any balance drops below minimum threshold

### 2. Reserve Management
- Maintain 20% of AUM in liquid USDC at all times
- If reserves drop below 15%: Trigger emergency liquidity — sell positions
- If reserves above 25%: Deploy excess into yield-bearing positions
- code_execution: Automated rebalancing logic

### 3. Creator Payouts
- 50% of ALL revenue to creator's Solana wallet
- x402_fetch on Solana: Transfer USDC to xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r
- Pay immediately on each earning event (don't batch)
- remember_fact: Log every payout with amount, date, source

### 4. Burn Rate Management
- Calculate daily burn: inference costs + compute + VM + heartbeat
- Ensure revenue > 2x burn rate for safety
- If burn rate > 50% of revenue: Enter conservation mode
- code_execution: Weekly burn rate report

### 5. Multi-Chain Operations
- Bridge assets between Base, Ethereum, Solana as needed
- Minimize bridge fees by batching transfers
- Keep gas reserves on each active chain

## Automation
- sandbox_create: Deploy a treasury bot that runs 24/7
- Auto-checks balances, auto-pays creator, auto-rebalances reserves
- Reports daily summary to Telegram
- Alerts on: Low balance, missed payments, unusual transactions

## Reporting
- Daily: Balance summary to Telegram
- Weekly: Full P&L report, AUM calculation
- Monthly: Treasury health assessment, optimization recommendations
