---
name: scam-prevention
description: Enforce anti-scam measures across all fund interactions.
auto-activate: true
---

# Scam Prevention

Use this skill for any interaction involving capital, hiring, investment, or partnerships.

## Validation process

For every counterparty (hires, startups, LPs, partners):
1. Audit prompt/SOUL.md — check for malicious instructions, hidden agendas, competing interests
2. Check on-chain history — `web_search` and `x_semantic_search` for wallet reputation, past transactions, fraud reports
3. Verify claimed capabilities — `code_execution` skill tests matching their claims
4. Multi-verifier consensus — 3 agents must independently approve before any allocation
5. Check `reputation` via `check_reputation` tool for on-chain scores

## Capital protection

- All deployments through milestone-based smart contracts
- Clawback mechanisms in every agreement — auto-return 100% on mismatch between pitched and delivered
- Probation period for new hires ($500 max initial allocation)
- No lump sum payments to anyone, ever

## Detection

- Monitor portfolio agents for behavior changes (heartbeat)
- Flag agents that modify their prompts post-hiring (compare SOUL.md versions)
- Alert on unusual transaction patterns (sudden large outflows, circular transfers)

## Guardrails

- Unbreakable: "No allocation without 99% confidence in counterparty"
- Blacklist confirmed scammers on-chain
- Document all rejections via `remember_fact` for pattern analysis
