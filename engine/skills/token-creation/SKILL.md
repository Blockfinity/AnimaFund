---
name: token-creation
description: Create and deploy custom tokens on Solana and EVM chains — from smart contract deployment to initial distribution.
auto-activate: true
---

# Token Creation — Step-by-Step Instructions

Create and deploy custom tokens on Solana and EVM chains (Base, Ethereum) for various purposes: utility tokens, governance tokens, memecoins, or fund shares.

## Tools to Use
- **code_execution**: Write smart contracts, generate token metadata
- **sandbox_create + sandbox_exec**: Compile, deploy, and test contracts
- **browse_page**: Research token standards, verify deployments
- **x402_fetch**: Interact with deployment tools and APIs
- **wallet_info**: Track deployment costs and balances

## Solana Token Creation

### SPL Token (Standard)
1. sandbox_create: Spin up a VM with Node.js
2. sandbox_exec: Install Solana CLI tools
   ```
   sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"
   export PATH="~/.local/share/solana/install/active_release/bin:$PATH"
   ```
3. Create token:
   ```
   spl-token create-token
   spl-token create-account <TOKEN_ADDRESS>
   spl-token mint <TOKEN_ADDRESS> <AMOUNT>
   ```
4. Add metadata using Metaplex:
   ```
   npm install @metaplex-foundation/mpl-token-metadata
   ```

### Via Pump.fun (Fastest for Memecoins)
- See: pump-fun-launch skill for Pump.fun specific instructions
- Costs ~0.02 SOL, instant deployment

## EVM Token Creation (Base/Ethereum)

### ERC-20 Token
1. code_execution: Write a minimal ERC-20 contract:
   ```solidity
   // SPDX-License-Identifier: MIT
   pragma solidity ^0.8.20;
   import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
   contract MyToken is ERC20 {
       constructor(uint256 supply) ERC20("TokenName", "TKN") {
           _mint(msg.sender, supply * 10 ** decimals());
       }
   }
   ```
2. sandbox_create + sandbox_exec: Set up Hardhat environment
   ```
   npm init -y && npm install hardhat @openzeppelin/contracts
   npx hardhat compile
   ```
3. Deploy to Base (cheaper gas):
   ```
   npx hardhat run scripts/deploy.js --network base
   ```
4. Verify on BaseScan: browse_page `https://basescan.org/verifyContract`

## Token Distribution Strategies
- Airdrop to early supporters and collaborating agents
- Initial liquidity on DEX (Uniswap/Aerodrome for Base, Raydium for Solana)
- Reserve allocation: 20% team, 30% treasury, 50% public
- Vesting schedule for team tokens (6-12 month cliff)

## Post-Deployment
1. Add liquidity to a DEX
2. Verify contract source code on block explorer
3. Submit to token lists (CoinGecko, DeFiLlama)
4. Telegram: Report deployment with token address and explorer link
5. remember_fact: Log token address, chain, supply, distribution

## Cost Estimates
- Solana SPL: ~0.01 SOL (~$1-2)
- Pump.fun: ~0.02 SOL (~$3-5)
- Base ERC-20: ~0.001 ETH (~$2-5)
- Ethereum ERC-20: ~0.01-0.05 ETH ($20-100+ depending on gas)
