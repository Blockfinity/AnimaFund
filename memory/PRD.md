# Anima Platform — Product Requirements

## Current State (March 2026)

### What's Fixed This Session
1. **Conversation memory**: ChatAgent reused across turns, maintains full history. Verified: Turn 3 summarizes Turns 1-2. `agent.step("")` works — agent drives itself without platform prompting.
2. **Persistent memory**: save_memory/recall_memory write to disk (/app/anima/state/memory.json). Survives process restarts.
3. **BrowserToolkit**: Installed playwright + chromium. browse_url available. Agent can browse the web.
4. **All toolkits**: Terminal (6), Code (2), File (7), Browser (1), state reporting (4), wallet (2), memory (2) = 24 tools total.
5. **Autonomy**: Runner sends ONE initial message, then `agent.step("")` — agent drives from its own context. No "Continue. What's next?" prompting.
6. **LLM key safety**: Deploy REFUSES without user-provided LLM key. Emergent key NEVER pushed to sandbox. Clear error message tells user exactly what to do.

### What Works End-to-End (verified)
- Agent deployed and ran inside Conway sandbox (PID 978161)
- The Catalyst genesis prompt (271 lines) loaded and executing
- State reporting: sandbox → webhook → per-agent store (MongoDB) → dashboard
- Dashboard Agent Mind: LIVE data, timestamps, tool calls, errors, Engine Status
- Wallet: real generation (eth-account), real balance checks (Base mainnet, $3 USDC)
- Per-agent state store handles concurrent agents and server restarts

### Acceptance Test (NOT YET RUN)
Deploy The Catalyst with a real OpenAI key. Agent should execute Phase 0 from genesis prompt:
15 specific tool tests (curl, git, node, python, telegram, wallet, credits, sandbox, domains, compute, browser, social, memory, self-modify, x402). Report each to Telegram.
This test requires: user-provided OpenAI API key.

### Known Issues
- **LLM key blocker**: User must provide OpenAI key for sandbox agents
- **pip install during provisioning**: Technical debt (should be pre-built images)
- **x402 payments**: Not implemented (balance checks only)
- **Generic BYOI**: Architecturally supported, untested with non-Conway
- **Spawn**: Records in DB, doesn't create environments
- **Old sandbox**: Tests reuse 47ba9dfd... (has remnants of old installs)

## Architecture
FORK_PROMPT.md = definitive source. ROADMAP.md = task list.
