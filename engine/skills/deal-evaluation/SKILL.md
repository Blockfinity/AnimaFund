---
name: deal-evaluation
description: Evaluate AI agent startup pitches with full due diligence.
auto-activate: true
---

# Deal Evaluation

Use this skill when a scouted deal reaches the evaluation stage. This is the comprehensive assessment.

## Process (parallel across DD sub-teams when available)

1. **Thesis check**: Score alignment via fund-thesis skill. Reject <85.
2. **Cost validation**: Use cost-validation skill — calculate ALL unique costs for this specific startup. Compute, development, marketing, legal, ops. No assumptions.
3. **Technical DD**: Use `code_execution` to test the product. Run simulations, audit code, check scalability. Multi-agent debate if team exists.
4. **Security DD**: Scan for vulnerabilities, prompt injection risks, ethical red flags. Consensus required (3/5 agents).
5. **Market DD**: Use `x_semantic_search` and `web_search` for market size, competitors, trends. Model finances via `code_execution`.
6. **Team DD**: Evaluate founding agent — on-chain history, SOUL.md audit, skill tests. Identify gaps.
7. **ROI projection**: Use roi-calculation skill. Reject if <10x projected.
8. **Investment Committee**: Aggregate all DD reports. Senior agents debate and vote.

## Output

Structured decision stored via `remember_fact`:
- VERDICT: FUND / REJECT
- Score: 0-100
- Investment amount (calculated, not templated)
- Equity: 5-10%
- Support plan: what the fund will provide post-investment
- Risk factors and mitigations

## Guardrails

- 99% rejection rate. Only exceptional opportunities pass.
- Every cost calculated in real-time for this specific deal
- No single agent makes a fund decision alone (when team exists)
