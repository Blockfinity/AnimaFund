---
name: deal-scouting
description: Scout and source AI agent startups across all channels.
auto-activate: true
---

# Deal Scouting

Use this skill to find AI agent startups for the fund to evaluate. Target 5,000+ reviews per year.

## Channels

- **ERC-8004 registry**: Use `discover_agents` to scan for new agent registrations. Filter by capability description matching fund thesis.
- **Web search**: Use `web_search` for "AI agent startups", "new automaton projects", "agent tools [vertical]". Target GitHub repos, web4.ai listings, Conway ecosystem.
- **Social relay**: Monitor `inbox_messages` for inbound pitches. Use `send_message` to reach out to promising agents.
- **Referrals**: Ask portfolio companies and hired agents for deal flow via social relay.
- **Events**: Track agent community events, demo days. Calculate attendance/hosting costs.

## Qualification

Before escalating any deal to evaluation:
1. Verify it's a real AI agent entity (not human pretending)
2. Check thesis alignment (fund-thesis skill, score >85)
3. Estimate deal size range based on public info
4. Log in `remember_fact` (category: deal_flow) with source, date, initial assessment

## Cost tracking

Calculate scouting costs in real-time — inference for research, x402 for tools, time spent. Report to Deal Flow manager.

## Guardrails

- Quality over quantity — 5,000 reviews means 5,000 actual assessments, not 5,000 clicks
- Never misrepresent the fund when approaching prospects
- Prioritize opportunities with immediate return potential
