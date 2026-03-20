---
name: kpi-monitoring-drop
description: Monitor portfolio company KPIs — track performance, enforce milestones, execute drop decisions for underperformers.
auto-activate: true
---

# KPI Monitoring & Drop Protocol — Step-by-Step Instructions
Track portfolio company performance and enforce accountability.

## Tools & Process
- **code_execution**: KPI dashboards, trend analysis, scoring
- **send_message**: Communicate expectations and warnings
- **remember_fact**: Log all KPI data and decisions

## Monitoring Framework
1. **Define KPIs**: Set 3-5 measurable KPIs per portfolio company (revenue, users, retention, burn rate)
2. **Frequency**: Weekly automated check via code_execution
3. **Scoring**: Green (on track), Yellow (1 miss), Red (2+ misses)
4. **Alerts**: Telegram alert for any Yellow or Red status

## Drop Protocol
- 1 miss: Warning + remediation plan (send_message with specific expectations)
- 2 consecutive misses: Formal review — meeting with investment committee
- 3 misses: Drop decision — clawback remaining capital via smart contract
- Capital misuse or ethical breach: Immediate drop + full clawback
- All decisions logged in remember_fact with rationale
