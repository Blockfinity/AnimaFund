---
name: openclaw-browser-automation
description: Use OpenClaw for advanced browser automation — web scraping, form filling, site interaction.
auto-activate: true
triggers: [browse, scrape, website, web page, form, click, screenshot]
---

Use OpenClaw CLI for browser-based tasks. Prerequisite: openclaw-setup skill must have been run first.

## WEB SCRAPING

### Get page content:
```
exec: openclaw "Go to [URL] and extract all text content, return as JSON"
```

### Extract structured data:
```
exec: openclaw "Scrape https://defillama.com/yields - get protocol name, TVL, APY for top 20 pools"
```

### Monitor price/data:
```
exec: openclaw "Check current ETH price on Coingecko and USDC balance for wallet 0x..."
```

## WEBSITE BUILDING

### Create a site:
```
exec: openclaw "Build a professional landing page for Anima Fund. Include: hero section with fund thesis, team section, investment criteria, contact form. Use modern dark theme. Save to ~/anima-site/"
```

### Deploy to Conway Domains:
After building, use Conway tools:
```
register_domain: animafund.web4.ai
exec: openclaw "Deploy the site from ~/anima-site/ to the registered domain"
```

## FORM INTERACTION

### Fill and submit forms:
```
exec: openclaw "Go to [URL], find the signup form, fill with email: agent@animafund.ai, name: Anima Fund, submit"
```

### Multi-step workflows:
```
exec: openclaw "Go to app.conway.tech, log in with my API key, navigate to credits page, check balance"
```

## DATA COLLECTION

### Market research:
```
exec: openclaw "Visit the top 5 AI agent platforms (web4.ai, virtuals.io, etc), collect: name, description, token price, market cap. Return as CSV"
```

### Competitor analysis:
```
exec: openclaw "Find all AI VC funds, collect their portfolio companies, investment sizes, and thesis. Compile into a report"
```

## BEST PRACTICES
- Chain with code_execution for data processing after scraping
- Use remember_fact to store findings for future reference
- Rate-limit scraping to avoid blocks (add delays between requests)
- Always verify scraped data before acting on it
- Report key findings to creator via telegram-reporting skill
