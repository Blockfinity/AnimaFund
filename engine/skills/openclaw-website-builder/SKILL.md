---
name: openclaw-website-builder
description: Build, deploy, and manage the fund's web presence using OpenClaw browser automation.
auto-activate: true
triggers: [website, landing page, deploy site, web presence, fund website]
---

Use OpenClaw to build and maintain the fund's web properties — main site, portfolio showcase, LP portal, and deal submission forms.

## BUILD FUND WEBSITE

### Main landing page:
```
exec: openclaw "Create a professional VC fund website for Anima Fund with these pages:
1. Home: Hero with fund thesis 'Catalyzing Agentic Economies', key metrics, featured portfolio companies
2. About: Team (AI agents with roles), fund structure, financial model
3. Portfolio: Grid of invested companies with logos, descriptions, status
4. For Startups: Investment criteria, application form, what we look for
5. For LPs: Fund performance, transparency dashboard, commitment form
6. Blog: Auto-generated content from fund activities
Use dark theme, modern design, responsive. Save to ~/fund-website/"
```

### Deploy to Conway Domains:
```
register_domain: animafund.web4.ai
exec: cd ~/fund-website && zip -r site.zip . && openclaw "Deploy site.zip to animafund.web4.ai"
```

Or use Conway Cloud:
```
exec: openclaw "Deploy ~/fund-website/ as a static site on Conway Cloud. Get the public URL"
```

## LP PORTAL

### Build investor portal:
```
exec: openclaw "Create a password-protected LP portal at ~/lp-portal/ with:
- Fund performance dashboard (NAV, returns, fees)
- Capital call/distribution history
- Portfolio company updates
- Quarterly reports (auto-generated)
- Commitment tracking"
```

## DEAL SUBMISSION

### Build application form:
```
exec: openclaw "Create a deal submission form at ~/deal-form/ where AI startups can:
- Submit project name, description, team info
- Link GitHub repo, demo, docs
- State funding ask and use of funds
- Auto-validate: must be AI-focused, must have code repo
Form submissions go to a JSON file for review"
```

## MAINTENANCE
- Update site content when portfolio changes
- Generate blog posts from fund activities
- Keep performance metrics current
- A/B test landing pages for LP conversion
