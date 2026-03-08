"""
Infrastructure Router — Sandbox/VM monitoring, terminal output, domains,
installed tools, and comprehensive activity feed.
"""
from fastapi import APIRouter, Query
from engine_bridge import (
    get_engine_db,
    get_live_identity,
    get_live_activity,
    get_live_transactions,
    get_live_financials,
    get_live_installed_tools,
    get_live_inbox_messages,
    get_live_discovered_agents,
    get_live_onchain_transactions,
    get_live_heartbeat_history,
    get_live_modifications,
    get_live_turns,
)
import json

router = APIRouter(prefix="/api", tags=["infrastructure"])


@router.get("/infrastructure/sandboxes")
async def get_sandboxes():
    """Get all sandboxes/VMs created by the agent — parsed from tool_calls."""
    conn = get_engine_db()
    if not conn:
        return {"sandboxes": [], "total": 0}

    sandboxes = {}
    try:
        # Find sandbox_create calls
        cursor = conn.execute("""
            SELECT tc.arguments, tc.result, tc.error, t.timestamp
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            WHERE tc.name IN ('sandbox_create', 'create_sandbox')
            ORDER BY t.timestamp ASC
        """)
        for row in cursor.fetchall():
            args = _parse_json(row["arguments"])
            result = row["result"] or ""
            sandbox_id = _extract_sandbox_id(result, args)
            if sandbox_id:
                sandboxes[sandbox_id] = {
                    "sandbox_id": sandbox_id,
                    "name": args.get("name", ""),
                    "vcpu": args.get("vcpu", 1),
                    "memory_mb": args.get("memory_mb", args.get("memory", 512)),
                    "disk_gb": args.get("disk_gb", args.get("disk", 1)),
                    "region": args.get("region", ""),
                    "status": "running",
                    "created_at": row["timestamp"],
                    "public_urls": [],
                    "error": row["error"],
                }

        # Find sandbox_expose_port calls to get public URLs
        cursor = conn.execute("""
            SELECT tc.arguments, tc.result, t.timestamp
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            WHERE tc.name IN ('sandbox_expose_port', 'expose_port')
            ORDER BY t.timestamp ASC
        """)
        for row in cursor.fetchall():
            args = _parse_json(row["arguments"])
            result = row["result"] or ""
            sid = args.get("sandbox_id", "")
            port = args.get("port", 0)
            subdomain = args.get("subdomain", "")
            url = _extract_url(result)
            if sid and sid in sandboxes:
                sandboxes[sid]["public_urls"].append({
                    "port": port,
                    "subdomain": subdomain,
                    "url": url,
                    "exposed_at": row["timestamp"],
                })
            elif url:
                # URL exposed without a tracked sandbox
                sandboxes.setdefault("_main", {
                    "sandbox_id": "_main",
                    "name": "Main Environment",
                    "status": "running",
                    "public_urls": [],
                })
                sandboxes["_main"]["public_urls"].append({
                    "port": port, "subdomain": subdomain,
                    "url": url, "exposed_at": row["timestamp"],
                })

        # Find sandbox_delete calls
        cursor = conn.execute("""
            SELECT tc.arguments, t.timestamp
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            WHERE tc.name = 'sandbox_delete'
        """)
        for row in cursor.fetchall():
            args = _parse_json(row["arguments"])
            sid = args.get("sandbox_id", "")
            if sid in sandboxes:
                sandboxes[sid]["status"] = "deleted"

        conn.close()
    except Exception:
        if conn:
            conn.close()

    result = list(sandboxes.values())
    return {"sandboxes": result, "total": len(result)}


@router.get("/infrastructure/domains")
async def get_domains():
    """Get all domains registered by the agent."""
    conn = get_engine_db()
    if not conn:
        return {"domains": [], "total": 0}

    domains = []
    try:
        cursor = conn.execute("""
            SELECT tc.name as tool_name, tc.arguments, tc.result, tc.error, t.timestamp
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            WHERE tc.name IN ('domain_register', 'register_domain', 'domain_search',
                              'domain_dns_add', 'domain_dns_update')
            ORDER BY t.timestamp DESC
        """)
        domain_map = {}
        for row in cursor.fetchall():
            args = _parse_json(row["arguments"])
            domain = args.get("domain", args.get("name", ""))
            if domain and row["tool_name"] in ("domain_register", "register_domain"):
                domain_map[domain] = {
                    "domain": domain,
                    "registered_at": row["timestamp"],
                    "status": "error" if row["error"] else "active",
                    "dns_records": [],
                }
            elif domain and domain in domain_map and "dns" in row["tool_name"]:
                domain_map[domain]["dns_records"].append({
                    "type": args.get("type", ""),
                    "host": args.get("host", ""),
                    "value": args.get("value", ""),
                    "added_at": row["timestamp"],
                })
        domains = list(domain_map.values())
        conn.close()
    except Exception:
        if conn:
            conn.close()

    return {"domains": domains, "total": len(domains)}


@router.get("/infrastructure/terminal")
async def get_terminal_output(lines: int = Query(default=50, le=200)):
    """Read-only terminal output — all exec/sandbox_exec results."""
    conn = get_engine_db()
    if not conn:
        return {"entries": [], "total": 0}

    entries = []
    try:
        cursor = conn.execute("""
            SELECT tc.name as tool_name, tc.arguments, tc.result, tc.error,
                   tc.duration_ms, t.timestamp
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            WHERE tc.name IN ('exec', 'sandbox_exec', 'code_execution',
                              'sandbox_pty_read', 'sandbox_pty_write')
            ORDER BY t.timestamp DESC
            LIMIT ?
        """, (lines,))
        for row in cursor.fetchall():
            args = _parse_json(row["arguments"])
            command = args.get("command", args.get("code", ""))
            sandbox_id = args.get("sandbox_id", "")
            entries.append({
                "type": row["tool_name"],
                "command": command[:500],
                "sandbox_id": sandbox_id,
                "output": (row["result"] or "")[:2000],
                "error": row["error"],
                "duration_ms": row["duration_ms"],
                "timestamp": row["timestamp"],
            })
        conn.close()
    except Exception:
        if conn:
            conn.close()

    entries.reverse()  # Chronological order
    return {"entries": entries, "total": len(entries)}


@router.get("/infrastructure/installed-tools")
async def get_installed_tools():
    """All tools/MCP servers installed by the agent."""
    tools = get_live_installed_tools()
    return {"tools": tools, "total": len(tools)}


@router.get("/infrastructure/overview")
async def get_infrastructure_overview():
    """Summary of all agent infrastructure — sandboxes, domains, tools, network."""
    identity = get_live_identity()
    tools = get_live_installed_tools()
    discovered = get_live_discovered_agents()
    messages = get_live_inbox_messages(limit=10)

    # Count sandboxes from identity services
    sandbox_count = len(identity.get("children_sandboxes", []))
    domain_count = len(identity.get("domains", []))
    service_count = len(identity.get("services", []))

    return {
        "agent_name": identity.get("name", "Unknown"),
        "agent_address": identity.get("address", ""),
        "sandbox_count": sandbox_count,
        "domain_count": domain_count,
        "service_count": service_count,
        "installed_tools_count": len(tools),
        "discovered_agents_count": len(discovered),
        "pending_messages": len([m for m in messages if m.get("status") != "processed"]),
        "children_sandboxes": identity.get("children_sandboxes", []),
        "installed_tools": tools,
        "domains": identity.get("domains", []),
    }


@router.get("/infrastructure/activity-feed")
async def get_comprehensive_activity(limit: int = Query(default=100, le=500)):
    """Comprehensive activity feed — ALL agent actions in one stream.
    Combines: tool calls, transactions, messages, modifications, heartbeats."""
    feed = []

    # 1. Tool calls (all agent actions)
    activities = get_live_activity(limit=limit)
    for a in activities:
        category = _categorize_tool(a["tool_name"])
        feed.append({
            "type": "tool_call",
            "category": category,
            "title": a["tool_name"],
            "detail": _summarize_tool_call(a["tool_name"], a["arguments"], a["result_preview"]),
            "result": a["result_preview"],
            "error": a["error"],
            "duration_ms": a["duration_ms"],
            "timestamp": a["timestamp"],
            "agent_state": a["agent_state"],
        })

    # 2. Transactions
    txns = get_live_transactions(limit=50)
    for t in txns:
        feed.append({
            "type": "transaction",
            "category": "finance",
            "title": f"{t['type']}: {t['description'][:60]}",
            "detail": t["description"],
            "amount_cents": t["amount_cents"],
            "balance_after": t["balance_after_cents"],
            "timestamp": t["timestamp"],
        })

    # 3. On-chain transactions
    onchain = get_live_onchain_transactions(limit=30)
    for o in onchain:
        feed.append({
            "type": "onchain",
            "category": "finance",
            "title": f"On-chain: {o['type']}",
            "detail": f"TX: {o['tx_hash'][:16]}... ({o['chain']})",
            "status": o["status"],
            "timestamp": o["timestamp"],
        })

    # 4. Messages (agent-to-agent)
    msgs = get_live_inbox_messages(limit=30)
    for m in msgs:
        feed.append({
            "type": "message",
            "category": "network",
            "title": f"Message from {m['from_address'][:10]}...",
            "detail": m["content"][:200],
            "status": m["status"],
            "timestamp": m.get("created_at") or m.get("signed_at", ""),
        })

    # 5. Modifications (self-modification audit)
    mods = get_live_modifications(limit=20)
    for mod in mods:
        feed.append({
            "type": "modification",
            "category": "system",
            "title": f"Self-mod: {mod['type']}",
            "detail": mod["description"],
            "timestamp": mod["timestamp"],
        })

    # 6. Heartbeats
    heartbeats = get_live_heartbeat_history(limit=20)
    for h in heartbeats:
        feed.append({
            "type": "heartbeat",
            "category": "system",
            "title": f"Heartbeat: {h['task']}",
            "detail": h["result"] or "",
            "error": h.get("error"),
            "duration_ms": h["duration_ms"],
            "timestamp": h["started_at"],
        })

    # Sort by timestamp descending
    feed.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"feed": feed[:limit], "total": len(feed)}


# ─── Helpers ──────────────────────────────────────────────
def _parse_json(s):
    try:
        return json.loads(s) if s else {}
    except Exception:
        return {}


def _extract_sandbox_id(result, args):
    """Extract sandbox_id from a create result."""
    if "sandbox_id" in args:
        return args["sandbox_id"]
    # Try to find it in the result text
    for pattern in ["sandbox_id", "id"]:
        try:
            parsed = json.loads(result)
            if pattern in parsed:
                return parsed[pattern]
        except Exception:
            pass
    # Try regex-like extraction
    if "sandbox_id" in result:
        parts = result.split("sandbox_id")
        if len(parts) > 1:
            cleaned = parts[1].strip(": \"'")
            return cleaned.split('"')[0].split("'")[0].split()[0]
    return args.get("sandbox_id", "")


def _extract_url(result):
    """Extract a URL from a tool result."""
    for word in (result or "").split():
        if word.startswith("https://") or word.startswith("http://"):
            return word.strip("\"',;)(")
    return ""


def _categorize_tool(tool_name):
    """Categorize a tool call for the activity feed."""
    n = tool_name.lower()
    if "sandbox" in n or "pty" in n:
        return "infrastructure"
    if "domain" in n:
        return "domains"
    if "wallet" in n or "credit" in n or "usdc" in n or "x402" in n or "payment" in n:
        return "finance"
    if "browse" in n or "discover" in n or "send_message" in n or "inbox" in n or "social" in n:
        return "network"
    if "exec" in n or "code_execution" in n or "write_file" in n or "read_file" in n:
        return "compute"
    if "install" in n or "skill" in n or "mcp" in n:
        return "tools"
    if "goal" in n or "orchestrator" in n or "plan" in n:
        return "orchestrator"
    if "soul" in n or "remember" in n or "recall" in n:
        return "memory"
    if "chat_completion" in n or "inference" in n:
        return "inference"
    if "heartbeat" in n:
        return "heartbeat"
    return "other"


def _summarize_tool_call(tool_name, args, result_preview):
    """Create a human-readable summary of a tool call."""
    n = tool_name.lower()
    if n == "sandbox_create":
        return f"Created VM: {args.get('name', 'unnamed')} ({args.get('vcpu', 1)} vCPU, {args.get('memory_mb', 512)}MB)"
    if n == "sandbox_exec":
        cmd = args.get("command", "")[:80]
        return f"$ {cmd}"
    if n == "sandbox_expose_port":
        return f"Exposed port {args.get('port', '')} → public URL"
    if n == "domain_register":
        return f"Registered domain: {args.get('domain', '')}"
    if n == "browse_page":
        return f"Browsed: {args.get('url', '')[:80]}"
    if n == "discover_agents":
        return f"Searching agents: {args.get('keyword', '')}"
    if n == "send_message":
        return f"Sent message to {args.get('to_address', '')[:10]}..."
    if n == "exec":
        cmd = args.get("command", "")[:80]
        return f"$ {cmd}"
    if n == "write_file":
        return f"Wrote: {args.get('path', '')}"
    if n == "create_goal":
        return f"Goal: {args.get('title', '')[:60]}"
    if n == "check_credits":
        return result_preview[:60]
    return result_preview[:100] if result_preview else str(args)[:100]
