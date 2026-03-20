# Anima Platform — Product Requirements

## Product
A platform to launch, monitor, and manage fully autonomous AI agents (Animas) in sandboxed environments.

## Current State (March 2026)

### What's ACTUALLY Working
- Anima Machina agent deployed and running INSIDE Conway sandbox (PID 978161, 179MB RAM)
- The Catalyst's full 271-line genesis prompt loaded and executing
- Agent made real LLM calls (gpt-4o-mini via Emergent proxy) for ~8 turns before hitting key restriction
- StateReportingToolkit successfully pushes data from sandbox → platform webhook → dashboard
- Dashboard Agent Mind page shows LIVE timestamped data from the sandbox agent
- WalletToolkit generates real wallets, checks real balances on Base mainnet ($3 USDC)
- Per-agent state store (cache + MongoDB) handles restart and concurrent agents
- Spawn API endpoint exists (/api/spawn/request) and records in MongoDB
- Cleanup verified: 448MB bloat deleted, 4,100 lines dead code archived

### What's NOT Working
- **Emergent Universal Key blocked from external VMs**: "Free users can only use Universal Key from within Emergent platform." Agent needs its own OpenAI/Anthropic key OR user needs paid Emergent plan for external access.
- **x402 payments**: Balance checks work, payments don't
- **Generic BYOI**: provision.py works with Conway but not truly generic
- **Spawn not provisioning**: Endpoint records requests but doesn't create environments
- **Agent hit error loop after turn 8**: Same turn prompt repeated 9 times (runner bug — should vary prompts)

### BLOCKER: LLM Key for Sandbox Agents
The Emergent Universal Key only works from within the Emergent platform server. Agents running in external sandboxes (Conway, Fly.io, etc.) need:
- Option A: User provides their own OpenAI/Anthropic API key (stored per-agent in MongoDB, pushed during deploy)
- Option B: User upgrades Emergent plan to enable external access
- Option C: Route sandbox agent LLM calls through the platform server (proxy)

### Next Priority
1. Resolve LLM key constraint for sandbox agents
2. Fix runner to not repeat same prompt (vary between turns, maintain conversation history)
3. Add more tools (BrowserToolkit, TerminalToolkit from CAMEL) so agent can DO things
4. x402 payments
5. Generic BYOI with mock provider test

## Architecture
See /app/docs/FORK_PROMPT.md (definitive source of truth)
See /app/docs/ROADMAP.md (authoritative task list)
