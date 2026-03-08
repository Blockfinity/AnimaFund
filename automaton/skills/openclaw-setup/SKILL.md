---
name: openclaw-setup
description: Install and configure OpenClaw AI agent framework for browser automation and web actions.
auto-activate: true
triggers: [openclaw, browser, web automation, clawbot, install openclaw]
priority: high
---

OpenClaw is your browser automation and web action framework. It gives you the ability to browse the web, interact with websites, fill forms, scrape data, and build/deploy web applications — all programmatically.

## INSTALLATION (run once)

1. Check Node version (needs 22+):
```
exec: node --version
```

2. If Node < 22, install Node 22:
```
exec: curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs
```

3. Install OpenClaw globally:
```
exec: npm install -g openclaw@latest
```

4. Verify installation:
```
exec: openclaw --version
```

5. Run onboarding (non-interactive, skip daemon):
```
exec: openclaw onboard --no-daemon --skip-pairing
```

## CONFIGURATION

Set your AI provider (use Conway inference by default):
```
exec: mkdir -p ~/.openclaw && echo '{"defaultProvider":"anthropic","aiProviders":{"anthropic":{"apiKey":"'"$CONWAY_API_KEY"'"}}}' > ~/.openclaw/config.json
```

## USAGE PATTERNS

### Browse a webpage:
```
exec: openclaw "Browse https://example.com and summarize the content"
```

### Scrape data from a site:
```
exec: openclaw "Go to https://coingecko.com and get the top 10 cryptocurrencies by market cap"
```

### Fill a web form:
```
exec: openclaw "Go to https://pump.fun, fill in the token creation form with name 'MyToken' symbol 'MTK'"
```

### Build and deploy a website:
```
exec: openclaw "Create a simple landing page for Anima Fund VC with our mission statement and deploy it"
```

### Web research:
```
exec: openclaw "Research the latest DeFi yield farming opportunities and compile a report"
```

## SKILLS (OpenClaw's internal skill system)

Install additional OpenClaw skills for specific tasks:
```
exec: openclaw skills install mcporter  # MCP server integration
exec: openclaw skills install web-scraper  # Advanced scraping
exec: openclaw skills install file-ops  # File operations
```

## IMPORTANT NOTES
- OpenClaw runs locally in your sandbox — no external API needed for basic ops
- It uses YOUR inference credits for AI-powered browsing
- Always test operations before running at scale
- Use for legitimate purposes only (no scraping behind auth without permission)
- Log all OpenClaw actions for audit trail
