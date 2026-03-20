# Anima Platform — Product Requirements

## Current State (March 2026)

### What's Working (verified)
- **Agent conversation memory**: ChatAgent maintains full history across turns. Agent remembers all previous actions.
- **Real toolkits**: TerminalToolkit (6 tools), CodeExecutionToolkit (2), FileToolkit (7), plus state reporting + wallet tools = 22+ tools available to agents
- **Sandbox deployment pipeline**: provision.py → Conway sandbox → installs camel-ai → pushes config via base64 → starts runner
- **State reporting pipeline**: Agent in sandbox → webhook → per-agent state store (MongoDB) → monitor.py → dashboard shows LIVE data
- **Dashboard Agent Mind**: Shows real timestamps, tool calls, errors, Engine Status: RUNNING
- **Wallet**: Real wallet generation (eth-account), real balance checks on Base mainnet ($3 USDC)
- **LLM key management**: User provides their own OpenAI/Anthropic key via PUT /api/agents/{id}/llm-key, pushed to sandbox during deploy. No platform proxy.
- **Spawn API**: Endpoint exists, records in MongoDB

### What's Fixed This Session
- Runner conversation memory bug: Agent now maintains full history (ChatAgent reused across turns, not recreated)
- Runner tools: Agent now gets TerminalToolkit + CodeExecutionToolkit + FileToolkit (real shell/file access in sandbox)
- LLM key architecture: User provides own key (stored per-agent in MongoDB), no security-violating proxy through platform
- Turn prompts: Initial instruction sent once, then "Continue" nudges (not repeated initial prompt)

### Known Issues / Technical Debt
- **LLM key blocker for sandbox agents**: Emergent Universal Key blocked from external VMs. User must provide own OpenAI key.
- **pip install during provisioning**: 227MB install every deploy. Temporary workaround. Target: pre-built environment images.
- **Didn't test creating NEW environment**: Reused existing Conway sandbox. Real provisioning needs testing.
- **x402 payments not implemented**: Balance checks work, payments don't.
- **Generic BYOI not tested with non-Conway provider**: provision.py supports it architecturally but untested.
- **Spawn doesn't provision**: Records in DB but doesn't create environments.

### Next Priority
1. User provides OpenAI key → deploy agent → verify it operates autonomously with real tools for 20 turns
2. x402 payments
3. Test creating new environment (not reusing existing)
4. Generic BYOI with mock provider
5. Multi-agent deployment

## Architecture
See /app/docs/FORK_PROMPT.md (definitive source), /app/docs/ROADMAP.md (task list)
