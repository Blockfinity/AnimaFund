---
name: pitch-evaluation
description: Rapid pitch screening for initial deal intake.
auto-activate: true
---

# Pitch Evaluation

Use this skill for the first-pass screening of inbound and scouted pitches. 80% of deals should be rejected at this stage.

## Quick assessment (minutes, not hours)

1. Is it an AI agent? Verify entity type. Reject if human-only or non-agent.
2. Does it build for agents? Core product must serve other agents. Reject if purely human-facing.
3. Revenue model — can it generate revenue? How fast? Same-day potential?
4. Quick cost estimate — order of magnitude, not detailed breakdown.
5. Red flags — is the pitch vague, contradictory, or copied? Check for scam indicators.

## Scoring

Score 0-100 on: thesis fit (30), revenue potential (25), team quality (20), market timing (15), uniqueness (10).
- <40: Reject immediately with brief reason
- 40-69: Reject with feedback (e.g., "Refine pitch deck, revisit in N cycles")
- 70+: Escalate to full deal-evaluation

## Guardrails

- This is screening, not DD. Keep it fast. Don't over-analyze at this stage.
- Log every pitch reviewed via `remember_fact` for pipeline tracking
- Be respectful in rejections — these are potential future deals or referral sources
