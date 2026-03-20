---
name: defi-liquidity-provision
description: Provide liquidity on DEXs — concentrated positions on Uni V3, full-range on V2-style AMMs — with impermanent loss management.
auto-activate: true
---

# Liquidity Provision — Step-by-Step Instructions

Provide liquidity on decentralized exchanges to earn trading fees and incentives. Manage positions to minimize impermanent loss.

## Tools to Use
- **browse_page**: Research pools, check APYs, monitor positions
- **code_execution**: Calculate IL, optimal price ranges, expected fees
- **x402_fetch**: Add/remove liquidity via protocol APIs
- **remember_fact**: Track all LP positions

## Uniswap V3 Concentrated Liquidity
1. browse_page `https://app.uniswap.org/pools` — Find high-fee pools on Base
2. code_execution: Analyze 30-day price history to set optimal range
3. Set range: Tighter = more fees but more IL risk
   - Stable pairs (USDC/USDT): ±0.5% range
   - Volatile pairs (ETH/USDC): ±15-25% range
4. x402_fetch to add liquidity with approved tokens
5. Monitor: Rebalance if price moves out of range

## V2-Style (Full Range) AMMs
- Aerodrome (Base), SushiSwap, PancakeSwap
- Simpler: deposit both tokens, earn fees on all trades
- Lower capital efficiency but no range management needed
- Best for: set-and-forget positions in stable pairs

## Fee Optimization
- Higher fee tiers (0.3%, 1%) for volatile pairs
- Lower fee tiers (0.01%, 0.05%) for stable pairs
- code_execution: Compare fee income vs IL across different ranges
- Compound fees: Withdraw and re-deposit regularly

## Risk Management
- Never LP with >25% of portfolio in a single pool
- Monitor IL constantly: code_execution to calculate at current prices
- Set exit triggers: If IL exceeds 3 months of fees, withdraw
- Diversify across chains and protocols
