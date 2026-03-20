# Anima Platform — Product Requirements

## Current State (March 2026)

### Verified This Session
1. **BrowserToolkit**: Uses real Playwright with LLM-driven multi-step navigation (planning, observation, action execution). NOT a curl wrapper. Requires LLM key in environment.
2. **agent.step("")**: Verified — agent drives itself from conversation history. Turn 1: runs uname. Turn 2 (empty): decides to run pwd. Turn 3 (empty): decides to ls /app. Each turn builds on previous.
3. **MemoryToolkit**: CAMEL native — save/load full conversation state to JSON. Registered with agent for persistent memory.
4. **Conversation persistence**: Agent saves state every 5 turns to /app/anima/state/conversation.json. On restart, loads previous state and continues.
5. **LLM key safety**: Deploy REFUSES without user-provided key. Returns clear error message.

### Complete Tool Inventory for Sandbox Agent
- TerminalToolkit: shell_exec, shell_view, shell_write_content_to_file, shell_write_to_process, shell_kill_process (6)
- CodeExecutionToolkit: execute_code, execute_command (2)
- FileToolkit: write_to_file, read_file, edit_file, search_files, glob_files, grep_files, notebook_edit_cell (7)
- BrowserToolkit: browse_url (Playwright multi-step, 1 entry point but full page interaction)
- MemoryToolkit: save, load, load_from_path, clear_memory (4 — CAMEL native)
- State reporting: report_state, report_action, report_error, report_financial (4)
- Wallet: create_wallet, check_balance (2)
- Persistent KV: save_memory, recall_memory (2)
Total: 28 tools

### Acceptance Test (blocked on OpenAI key)
Phase 0 from The Catalyst genesis prompt: 15 tool tests with real usage, report each to Telegram.
User must provide OpenAI API key via: PUT /api/agents/anima-fund/llm-key

### Dashboard: Single-Agent → Multi-Agent (after acceptance test)
Current dashboard monitors one agent. Needs:
- Multi-agent overview (all Animas at once)
- Agent selector drill-down
- Parent-child lineage
- Aggregate views (total revenue, costs)
- Ultimus screens (goal input, Dimensions, execute)
Foundation exists: per-agent state store in agent_state_store.py + monitor.py

### Ultimus (CORE — not backlog)
Prerequisites: acceptance test pass → x402 payments → generic BYOI → spawn
Then: predictor → calculator → executor → Dimensions → 4 seed data modes → frontend screens

## Architecture
FORK_PROMPT.md = definitive source. ROADMAP.md = task list.
