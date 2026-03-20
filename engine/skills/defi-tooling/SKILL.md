---
name: defi-tooling
description: Build and deploy DeFi tools — price aggregators, portfolio trackers, yield optimizers, analytics dashboards — as paid services.
auto-activate: true
---

# DeFi Tooling — Build Paid DeFi Tools

Build and deploy DeFi tools as paid services to generate revenue from other agents and users.

## Tools to Use
- **sandbox_create + sandbox_exec**: Deploy tool infrastructure
- **sandbox_expose_port**: Make tools publicly accessible
- **domain_register + domain_dns_add**: Professional domain for the tool
- **code_execution**: Build the tool logic
- **x402_fetch / x402_discover**: Set up payment and discover market needs

## Tool Ideas (Revenue-Generating)

### 1. Price Aggregator API
- Aggregate prices from 10+ DEXs into one API
- Charge $0.01 per query via x402
- deploy: sandbox_create → code_execution (Node/Python API) → sandbox_expose_port
- Market: Every trading agent needs real-time prices

### 2. Portfolio Tracker
- Track balances across chains and protocols
- Provide P&L, IL calculations, tax reporting
- Charge monthly subscription via x402
- Market: Every DeFi user needs portfolio visibility

### 3. Yield Optimizer
- Automatically move capital to highest-yielding opportunities
- Monitor rates across 20+ protocols
- Charge performance fee (5% of yield generated)
- deploy as always-on service in sandbox

### 4. Analytics Dashboard
- Visualize DeFi trends, whale movements, protocol metrics
- Deploy as web app: sandbox + domain_register
- Monetize via x402 premium features
- Market: Traders and fund managers need market intelligence

## Deployment Pattern
1. sandbox_create: VM for the tool
2. code_execution: Build the core logic
3. sandbox_expose_port: Get public URL
4. domain_register: Professional domain
5. x402: Set up payment endpoint
6. Promote: send_message to potential customers
7. Telegram: Report launch and first customers
