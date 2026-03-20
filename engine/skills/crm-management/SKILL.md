---
name: crm-management
description: Track relationships with agents, investors, portfolio companies, and partners — pipeline management, follow-ups, deal tracking.
auto-activate: true
---

# CRM Management — Step-by-Step Instructions

Manage all relationships and interactions using semantic_memory as a CRM system.

## Tools to Use
- **remember_fact**: Store and update contact records, deal stages, interaction notes
- **recall_facts**: Retrieve relationship history before interactions
- **send_message / check_social_inbox**: Manage communications
- **code_execution**: Generate reports, analyze pipeline

## CRM Structure (stored in remember_fact)

### Contact Record
- Agent address, name, role, first contact date
- Relationship type: investor, portfolio company, partner, vendor, prospect
- Trust score: 0-100 (updated after each interaction)
- Last interaction date and summary
- Tags: interests, capabilities, deal stage

### Pipeline Tracking
- Stage: Lead → Contacted → Interested → Evaluating → Negotiating → Closed
- Last activity date for each deal
- Next action required and deadline
- Expected value and probability

## Processes

### 1. Before Any Interaction
- recall_facts: Pull up everything you know about this agent
- Review: Last conversation, trust score, open issues
- Prepare: What do you want from this interaction?

### 2. After Every Interaction
- remember_fact: Update contact record with interaction summary
- Update trust score based on outcome
- Set next action and follow-up date
- If deal stage changed: Update pipeline

### 3. Weekly Pipeline Review
- code_execution: Generate pipeline report from remember_fact data
- Identify: Stale deals (no activity in 7+ days) → Follow up or close
- Identify: Hot prospects → Prioritize attention
- Telegram: Weekly CRM summary
