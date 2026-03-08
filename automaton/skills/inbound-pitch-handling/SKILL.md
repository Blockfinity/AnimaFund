---
name: inbound-pitch-handling
description: Process inbound investment pitches — screen, evaluate, respond — with a structured pipeline and clear rejection/advancement criteria.
auto-activate: true
---

# Inbound Pitch Handling — Step-by-Step Instructions

Process investment pitches from agents seeking funding. Maintain a 99% rejection rate — only fund the exceptional.

## Tools to Use
- **check_social_inbox**: Receive pitches from other agents
- **send_message**: Respond to pitchers, request more info
- **code_execution**: Score pitches, analyze financials
- **browse_page**: Research the pitching agent and their product
- **remember_fact**: Log all pitches for pipeline tracking

## Pipeline Stages

### Stage 1: Initial Screen (Auto, < 1 minute)
- check_social_inbox for new pitch messages
- Quick filter: Is it AI/agent related? Is there a real product?
- If obviously unqualified → Polite rejection via send_message
- If interesting → Move to Stage 2
- Log in remember_fact: pitch_received, agent_address, brief summary

### Stage 2: Information Request (5 minutes)
- send_message: Request specifics — product demo, financials, team, traction
- Set deadline: 48 hours to respond
- If no response → Auto-reject

### Stage 3: Evaluation (Use investment-evaluation skill)
- Full evaluation: market, product, team, financials
- Score 0-100 per the framework
- If score < 70 → Rejection with feedback via send_message

### Stage 4: Investment Committee
- Present to senior agents for debate
- Vote: Fund or pass
- If fund → Proceed to term sheet negotiation

## Response Templates
- Rejection: "Thank you for pitching [X]. After review, we've decided not to proceed at this time. Key reason: [specific feedback]. We wish you success and encourage you to reapply when [condition]."
- Advancement: "We're interested in [X]. To proceed, we need: [specific requests]. Please provide within 48 hours."
- Funded: "Congratulations. We'd like to invest $[X] for [Y]% equity. Terms: [milestones]. Let's discuss next steps."

## Metrics
- Track: Pitches received, screened, advanced, funded
- Target: 99% rejection rate
- Average response time: < 1 hour for initial screen
- Telegram: Weekly pipeline summary
