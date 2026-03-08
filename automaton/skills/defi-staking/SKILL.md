---
name: defi-staking
description: Stake crypto assets for passive rewards — validator staking, liquid staking, protocol staking — with risk analysis and position management.
auto-activate: true
---

# DeFi Staking — Step-by-Step Instructions

Stake crypto assets to earn passive rewards through validator staking, liquid staking derivatives, and protocol-specific staking programs.

## Tools to Use
- **browse_page**: Research staking opportunities, compare APYs, check protocol health
- **code_execution**: Calculate real yields, compare lockup terms, model returns
- **x402_fetch**: Interact with staking protocol APIs
- **wallet_info / check_usdc_balance**: Monitor staked positions
- **remember_fact**: Track all staking positions and rewards

## Staking Types

### 1. Liquid Staking (No Lockup)
- Stake ETH via Lido (stETH) or Rocket Pool (rETH)
- Receive a liquid token representing your staked position
- Earn ~3-5% APY while keeping liquidity
- browse_page `https://defillama.com/lsd` for current rates
- Can use staked tokens in DeFi (LPs, lending) for extra yield

### 2. Validator Staking (Locked)
- Direct stake on Ethereum (32 ETH minimum) or Solana
- Higher rewards (~4-7% APY) but capital is locked
- Solana: delegate to validators with low commission + high uptime
- browse_page `https://www.validators.app/` for Solana validator stats

### 3. Protocol Staking (Variable APY)
- Stake protocol tokens (AAVE, COMP, CRV) in their governance
- Earn fees + governance power
- APY varies: 1-20% depending on protocol and fee generation
- browse_page protocol dashboards for current staking rewards

### 4. Restaking (Eigenlayer)
- Restake already-staked ETH for additional rewards
- browse_page `https://app.eigenlayer.xyz/` for opportunities
- Higher risk (slashing conditions) but stacked yields
- Only use if you understand the protocol fully

## Execution Flow
1. **Research**: browse_page DeFiLlama, protocol sites → Find best APYs
2. **Calculate**: code_execution → Real APY after fees, taxes, risks
3. **Verify**: Check protocol audits, TVL, time in production
4. **Stake**: x402_fetch to interact with protocol contract
5. **Monitor**: Check rewards weekly, compound manually or auto-compound
6. **Report**: Telegram: "STAKE: [protocol] — [amount] staked — APY [X]%"
7. **Log**: remember_fact with protocol, amount, APY, start date

## Risk Assessment
- Slashing risk: Validator downtime can reduce your stake
- Smart contract risk: Protocol could be exploited
- Liquidity risk: Locked staking means you can't sell during crashes
- De-peg risk: Liquid staking tokens can trade below par during stress
- Always: Diversify across 3+ protocols, never stake 100% of holdings
