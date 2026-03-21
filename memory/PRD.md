# Anima Platform — Product Requirements

## Security Status (March 21 2026)
- FIXED: Sandbox only gets WEBHOOK_URL (specific endpoint), NOT platform base URL
- FIXED: Per-agent webhook token (32-byte hex) generated during deploy, validated by endpoint
- VERIFIED: env inside sandbox shows WEBHOOK_URL + WEBHOOK_TOKEN only, PLATFORM_URL=NOT_SET
- TODO: Enforce token validation (currently allows tokenless for dev), add JWT to all platform endpoints

## Acceptance Test Status
- Agent RUNNING in Conway sandbox (PID confirmed)
- Conway inference WORKING (gpt-5-mini, HTTP 200)
- Webhook pipeline WORKING (agent -> webhook -> dashboard, 32+ actions)
- Phase 0: 6/11 passed, 3 failed (Git auth, Python symlink, Browser path), 2 unverified
- Phase 0 NOT complete — agent self-reported complete but tests actually failed

## Fixes Still Needed (Before Phase 0 Re-run)
1. Git test: use public repo clone (no auth needed)
2. Python: create symlink python -> python3 during deploy
3. Browser: install playwright + chromium during deploy
4. Wallet: use existing Catalyst wallet (0x922868...), don't create new empty one
5. Credit exhaustion: graceful handling when credits hit $0

## Architecture
FORK_PROMPT.md = definitive source. ROADMAP.md = task list.
