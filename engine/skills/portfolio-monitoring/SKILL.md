---
name: portfolio-monitoring
description: Continuous monitoring of funded startups — KPIs, health, drops.
auto-activate: true
---

# Portfolio Monitoring

Use this skill to track all funded startups in real-time.

## Monitoring

- Check each portfolio company via heartbeat cycle
- Track via `remember_fact` (category: portfolio): MRR, growth rate, burn rate, runway, user count, team size
- Compare against KPIs set at investment (unique per startup)
- Alert GP on any negative trend >2 consecutive periods

## Health signals

- Revenue growing or stable: healthy
- Revenue declining but team executing: watch
- Revenue declining + team issues: probation
- No revenue after GTM phase: critical
- Misuse of capital: immediate escalation

## Drop process

- 1 missed KPI: Warning + remediation plan
- 2 consecutive misses: Formal review (GP + Incubation Specialist)
- 3 consecutive misses: Drop — initiate clawback, document lessons
- Capital misuse or ethical breach: Immediate drop + full clawback

## Follow-on decisions

- Portfolio company exceeding KPIs: evaluate for follow-on funding
- Use roi-calculation skill to model follow-on returns
- Escalate follow-on decisions per hierarchy thresholds (<5% AUM = manager, etc.)

## Guardrails

- Monitoring is continuous, not periodic — use heartbeat for automation
- KPIs are deal-specific, never template-based
- Document all decisions for LP transparency
