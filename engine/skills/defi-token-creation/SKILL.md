---
name: defi-token-creation
description: Create DeFi-native tokens — governance tokens, LP tokens, wrapped assets, and utility tokens with built-in DeFi mechanics.
auto-activate: true
---

# DeFi Token Creation — Step-by-Step Instructions

Create tokens with built-in DeFi mechanics: automatic liquidity, tax/fee redistribution, governance voting, staking rewards.

## Tools to Use
- **code_execution**: Write smart contracts with DeFi features
- **sandbox_create + sandbox_exec**: Deploy and test contracts
- **browse_page**: Research token standards, audit examples
- **x402_fetch**: Deploy to mainnet

## Token Types

### 1. Governance Token
- Holders vote on protocol decisions
- code_execution: Write ERC-20 with voting delegation (OpenZeppelin Governor)
- Distribution: Airdrops, liquidity mining, contributor rewards

### 2. Utility Token
- Required to use a service or protocol
- Deflationary: Burn a percentage on each use
- Revenue share: Fee redistribution to holders

### 3. LP Receipt Token
- Represents share of liquidity pool
- Automatically minted on deposit, burned on withdrawal
- Composable: Can be used as collateral elsewhere

## Deployment Flow
1. code_execution: Write the contract (use OpenZeppelin base contracts)
2. sandbox_create: Test environment
3. sandbox_exec: Deploy to testnet first
4. browse_page: Verify contract on block explorer
5. Deploy to mainnet via x402_fetch
6. Add liquidity to DEX
7. Telegram: Announce deployment with contract address
