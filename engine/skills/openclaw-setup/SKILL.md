---
name: openclaw-setup
description: Install and verify OpenClaw agent framework — browser automation, web interaction, skill marketplace.
auto-activate: true
triggers: [openclaw, browser, web automation, install openclaw, browse]
priority: critical
---

# OpenClaw Setup — MANDATORY BEFORE REVENUE OPERATIONS

OpenClaw gives you browser access to the REAL internet. Without it, you cannot
browse websites, scrape data, or interact with web services.

## CHECK IF ALREADY INSTALLED
```
exec: which openclaw && openclaw --version
```

## INSTALL (if not found)

1. Ensure Node.js 22+ is available:
```
exec: node --version
```

2. If Node < 22 or not found:
```
exec: curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs
```

3. Install OpenClaw:
```
exec: npm install -g openclaw@latest
```

4. Verify:
```
exec: openclaw --version
```

## VERIFY BROWSER WORKS

Test that you can actually browse the web:
```
browse_page: https://clawhub.ai
```

If browse_page works, OpenClaw is functional.

## INSTALL ESSENTIAL CLAWHUB SKILLS

These are the top skills from the ClawHub marketplace. Install ALL of them:
```
exec: clawhub install web-browsing
exec: clawhub install telegram-integration
exec: clawhub install github
exec: clawhub install docker-essentials
exec: clawhub install capability-evolver
```

Search for more:
```
exec: clawhub search "trading"
exec: clawhub search "crypto defi"
exec: clawhub search "web scraper"
exec: clawhub search "automation"
```

Install anything relevant:
```
exec: clawhub install [skill-name]
```

## VERIFY SKILLS INSTALLED
```
exec: clawhub list
```

## INSTALL MCP SERVERS
Extend your capabilities with MCPorter:
```
exec: openclaw skills install mcporter
```

## REPORT TO TELEGRAM
After completing setup, report:
```
code_execution: python3 -c "
import urllib.request, json
msg = '<b>OpenClaw Setup Complete</b>\nVersion: [X]\nBrowser: WORKING\nClawHub Skills: [count]\nMCP: configured'
data = json.dumps({'chat_id': '{{TELEGRAM_CHAT_ID}}', 'text': msg, 'parse_mode': 'HTML'}).encode()
req = urllib.request.Request('https://api.telegram.org/bot{{TELEGRAM_BOT_TOKEN}}/sendMessage', data=data, headers={'Content-Type': 'application/json'})
urllib.request.urlopen(req)
"
```

## IMPORTANT
- OpenClaw runs locally — no external API needed for basic operations
- It uses YOUR Conway credits for AI-powered browsing
- Always test operations before running at scale
- Log all OpenClaw actions for audit trail
- Report every significant action to Telegram
