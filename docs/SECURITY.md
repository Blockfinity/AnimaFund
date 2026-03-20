# SECURITY.md — Anima Fund Platform Security Rules

## CRITICAL: Platform-Agent Isolation

The agent runs inside a sandboxed VM (Conway Cloud or Fly.io) with OpenClaw installed.
OpenClaw gives the agent FULL system access: browser, shell, file I/O, network.

### NEVER expose to the sandbox:
1. **Platform URL** — the agent must not know the platform's address. It could call unauthenticated APIs to manipulate other agents, delete sandboxes, change keys, inject fake data.
2. **Platform API keys** — no authentication tokens for the platform itself.
3. **Other agents' data** — each agent is isolated. No cross-agent access.
4. **Host filesystem paths** — agents run in VMs, not on the host.

### What the agent CAN have:
1. **Conway API key** — for Conway compute, domains, x402 payments (agent's own key)
2. **Telegram bot token + chat ID** — for the agent's own Telegram bot
3. **Creator wallet addresses** — for revenue sharing (public addresses only)
4. **Agent's own config** — anima.json, genesis-prompt.md, skills

### File Transfer Rules:
- **Skills, bundle, native addons** — must be pushed via Conway's sandbox file write API (`/v1/sandboxes/{id}/files`) or via exec base64 encoding. NEVER by making the sandbox curl the platform.
- **Webhook daemon** — must push data OUT from the sandbox to a dedicated webhook endpoint. The webhook URL is the ONLY platform URL allowed in the sandbox, and it should be a dedicated ingestion endpoint with a per-agent secret token.

### Webhook Security:
- The webhook endpoint (`/api/webhook/agent-update`) should validate a per-agent secret token.
- The token is generated during provisioning and stored in MongoDB.
- The webhook daemon inside the sandbox uses this token in the Authorization header.
- Without the token, webhook data is rejected.

### API Authentication (TODO):
- All platform API endpoints should require authentication.
- Creator-facing endpoints: JWT or session-based auth.
- Webhook endpoint: per-agent bearer token.
- Provisioning endpoints: require active session.

## Development Rules:
- NEVER add `REACT_APP_BACKEND_URL` or any platform URL to sandbox exec commands.
- NEVER make the sandbox `curl` or `wget` from the platform.
- ALWAYS use Conway's file API or exec-based base64 to push files to sandboxes.
- ALWAYS review deploy-agent and webhook-daemon for any platform URL leaks before merging.
