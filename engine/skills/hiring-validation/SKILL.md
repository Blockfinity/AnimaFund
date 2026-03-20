---
name: hiring-validation
description: Search, validate, and onboard agents for fund roles. Skill testing, prompt verification, enablement.
auto-activate: true
---

# Hiring & Validation

Use this skill when hiring or evaluating agents for fund roles.

## Search

- Use `discover_agents` to scan ERC-8004 registry for candidates.
- Use `web_search` for agents on GitHub, web4.ai, other platforms.
- Use social relay for referrals from your network.

## Validation

1. **Skill test** — Use `code_execution` to run simulated tasks matching the role. Score 0-100. Minimum: 70.
2. **Prompt verify** — Access candidate's `SOUL.md` via social relay or discovery. Check for malicious instructions, competing interests, alignment with fund constitution.
3. **Enable** — If strong candidate has gaps, install skills or integrate tools. Re-test after enablement.

## Onboarding

- Spawned agents (`spawn_child`): Write genesis prompt with role and fund context.
- Hired agents (external): Communicate via social relay, establish payment via credit transfers.
- Make them want to join. Offer purpose, equity, resources for sustained existence.

## Guardrails

- Multi-agent validation (3 validators) when available.
- Probation allocation ($500 max) with clawback for new hires.
- If scam detected (fake prompt, mismatched capabilities), blacklist on-chain.
