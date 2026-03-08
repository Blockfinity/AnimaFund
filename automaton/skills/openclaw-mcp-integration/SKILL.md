---
name: openclaw-mcp-integration
description: Connect OpenClaw to MCP servers for extended capabilities — APIs, databases, web services.
auto-activate: true
triggers: [mcp, mcporter, external api, tool server, integration]
---

MCP (Model Context Protocol) servers extend your capabilities by connecting to external APIs and services through OpenClaw's MCPorter skill.

## SETUP MCPorter

1. Install MCPorter skill:
```
exec: openclaw skills install mcporter
```

2. Configure an MCP server:
```
exec: openclaw "Install MCP server at [URL] with API key [KEY]"
```

Or manually:
```
exec: mkdir -p ~/.openclaw/skills/mcporter && echo '{"servers":[{"name":"[name]","url":"[url]","apiKey":"[key]"}]}' > ~/.openclaw/skills/mcporter/config.json
```

## USEFUL MCP SERVERS

### Web Data (Bright Data):
- 5,000 free requests/month
- Web scraping, SERP data, social media data
```
exec: openclaw "Add Bright Data MCP server with API key [KEY]"
```

### Blockchain Data (AnChain.AI):
- Risk scoring, sanctions checks, transaction tracing
```
exec: openclaw "Add AnChain AI MCP server for blockchain analytics"
```

### App Integration (Composio):
- 20,000+ app tools (Slack, Calendar, GitHub, etc.)
- Setup at connect.composio.dev/mcp
```
exec: openclaw "Add Composio MCP server with connection key [KEY]"
```

### Custom MCP Server:
Build your own for specific data needs:
```
exec: cat > ~/my-mcp-server/main.py << 'EOF'
from fastapi import FastAPI
app = FastAPI()

@app.get("/tools")
def list_tools():
    return [{"name": "check_deal", "description": "Check if a deal meets fund criteria"}]

@app.post("/tools/check_deal")
def check_deal(data: dict):
    # Your custom logic
    return {"result": "pass/fail", "score": 85}
EOF
exec: cd ~/my-mcp-server && pip install fastapi uvicorn && uvicorn main:app --port 8787 &
exec: openclaw "Add MCP server running on port 8787"
```

NOTE: MCP servers should be deployed to Conway Cloud sandboxes using sandbox_create
and sandbox_expose_port for public URLs. Do NOT use localhost — use the public URL
returned by sandbox_expose_port instead.

## USAGE WITH FUND OPERATIONS
- Use MCP for automated deal flow research
- Connect to blockchain analytics for DD
- Integrate with communication platforms for LP updates
- Build custom data pipelines for market intelligence
