---
name: openclaw-deal-research
description: Use OpenClaw browser automation for deal flow research, due diligence, and market intelligence.
auto-activate: true
triggers: [deal research, due diligence, market research, competitor, startup, scout]
---

Leverage OpenClaw's web browsing for fund operations — scouting deals, running DD, and gathering market intelligence.

## DEAL SCOUTING

### Scan agent registries:
```
exec: openclaw "Browse web4.ai/agents and list all newly registered AI agents from the last 7 days. For each: name, description, capabilities, creator address"
```

### Check GitHub for AI projects:
```
exec: openclaw "Search GitHub for repositories with 'AI agent' created in last 30 days, sorted by stars. Get: repo name, description, stars, language, last commit date"
```

### Monitor social for signals:
```
exec: openclaw "Check X/Twitter for trending topics about AI agents, DeFi agents, and autonomous AI. Summarize top 10 discussions"
```

## DUE DILIGENCE

### Technical DD:
```
exec: openclaw "Go to [startup GitHub URL], analyze: code quality, commit frequency, test coverage, documentation quality, open issues. Score 0-100"
```

### Team DD:
```
exec: openclaw "Research [founder name/address] — find their GitHub profile, X account, LinkedIn, previous projects. Compile background report"
```

### Market DD:
```
exec: openclaw "Research the [vertical] market: size, growth rate, key players, recent funding rounds. Use Crunchbase, PitchBook, and news sources"
```

### Token/Contract DD:
```
exec: openclaw "Analyze smart contract at [address] on [chain]: check verified source, audit reports, token distribution, holder concentration, liquidity"
```

## MARKET INTELLIGENCE

### Weekly market report:
```
exec: openclaw "Compile weekly report: top AI funding rounds, new AI agent launches, DeFi TVL changes, crypto market trends. Format as markdown"
```

### Competitive analysis:
```
exec: openclaw "Find all AI VC funds (a16z AI, Paradigm, etc). For each: AUM, thesis, recent investments, team size, portfolio performance"
```

## WORKFLOW
1. Scout → 2. Initial screen → 3. Deep DD (if passes) → 4. Report to investment committee
- Store all findings via remember_fact for future reference
- Send key discoveries to creator via telegram-reporting
- Track all scouted deals in working memory
