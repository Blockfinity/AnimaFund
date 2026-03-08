"""
Anima Fund — Live Engine Bridge

Reads directly from the Automaton's SQLite state.db when the engine is running.
This is the REAL data pipeline — not demo data.

The Automaton engine writes to ~/.anima/state.db with these tables:
  - turns: Agent reasoning log (thinking, tools, tokens, cost)
  - tool_calls: Denormalized tool call results per turn
  - children: Spawned child automaton records
  - transactions: Financial transaction log
  - heartbeat_history: Task execution history
  - identity: Agent identity KV (name, address, creator, sandbox)
  - kv: General key-value store
  - modifications: Self-modification audit trail
  - skills: Installed skill definitions
  - inbox_messages: Social messages
  - spend_tracking: Financial spend by time window
  - inference_costs: Per-call inference cost tracking
  - child_lifecycle_events: Child state machine audit trail
  - soul_history: Versioned SOUL.md history
  - working_memory, episodic_memory, semantic_memory, procedural_memory, relationship_memory
"""
import os
import sqlite3
import json
from typing import Optional
from datetime import datetime, timezone


ANIMA_STATE_DB = os.path.expanduser("~/.anima/state.db")


def get_engine_db() -> Optional[sqlite3.Connection]:
    """Get a read-only connection to the live engine database."""
    if not os.path.exists(ANIMA_STATE_DB):
        return None
    try:
        conn = sqlite3.connect(f"file:{ANIMA_STATE_DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def is_engine_live() -> dict:
    """Check if the Automaton engine is running and has state."""
    db_exists = os.path.exists(ANIMA_STATE_DB)
    conn = get_engine_db()
    if not conn:
        return {"live": False, "db_exists": db_exists, "reason": "no state.db"}

    try:
        # Check if there are any turns (engine has actually run)
        cursor = conn.execute("SELECT COUNT(*) FROM turns")
        turn_count = cursor.fetchone()[0]

        # Get agent state
        cursor = conn.execute("SELECT value FROM kv WHERE key = 'agent_state'")
        row = cursor.fetchone()
        agent_state = row[0] if row else "unknown"

        # Get identity
        cursor = conn.execute("SELECT value FROM identity WHERE key = 'name'")
        row = cursor.fetchone()
        name = row[0] if row else "Unknown"

        conn.close()
        return {
            "live": turn_count > 0,
            "db_exists": True,
            "turn_count": turn_count,
            "agent_state": agent_state,
            "fund_name": name,
        }
    except Exception as e:
        conn.close()
        return {"live": False, "db_exists": db_exists, "reason": str(e)}


def get_live_agents() -> list:
    """Read child agents from the engine's children table."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT id, name, address, sandbox_id, genesis_prompt,
                   funded_amount_cents, status, created_at, last_checked, role
            FROM children ORDER BY created_at DESC
        """)
        agents = []
        for row in cursor.fetchall():
            role = row["role"] or "Agent"
            if not row["role"]:
                prompt = row["genesis_prompt"] or ""
                if "You are" in prompt:
                    role_part = prompt.split("You are")[1].split(".")[0].split(",")[0].strip()
                    role = role_part[:40]

            agents.append({
                "agent_id": row["id"],
                "name": row["name"],
                "role": role,
                "wallet_address": row["address"],
                "sandbox_id": row["sandbox_id"],
                "funded_cents": row["funded_amount_cents"],
                "status": row["status"],
                "created_at": row["created_at"],
                "last_checked": row["last_checked"],
            })
        conn.close()
        return agents
    except Exception:
        conn.close()
        return []


def get_live_activity(limit: int = 50) -> list:
    """Read recent tool calls from the engine — these are REAL agent actions."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT tc.id, tc.turn_id, tc.name as tool_name, tc.arguments,
                   tc.result, tc.duration_ms, tc.error,
                   t.timestamp, t.state
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            ORDER BY t.timestamp DESC
            LIMIT ?
        """, (limit,))
        activities = []
        for row in cursor.fetchall():
            args = {}
            try:
                args = json.loads(row["arguments"]) if row["arguments"] else {}
            except Exception:
                pass

            activities.append({
                "activity_id": row["id"],
                "turn_id": row["turn_id"],
                "tool_name": row["tool_name"],
                "arguments": args,
                "result_preview": (row["result"] or "")[:200],
                "duration_ms": row["duration_ms"],
                "error": row["error"],
                "timestamp": row["timestamp"],
                "agent_state": row["state"],
            })
        conn.close()
        return activities
    except Exception:
        conn.close()
        return []


def get_live_transactions(limit: int = 50) -> list:
    """Read financial transactions from the engine."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT id, type, amount_cents, balance_after_cents, description, created_at
            FROM transactions ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        txns = []
        for row in cursor.fetchall():
            txns.append({
                "id": row["id"],
                "type": row["type"],
                "amount_cents": row["amount_cents"],
                "balance_after_cents": row["balance_after_cents"],
                "description": row["description"],
                "timestamp": row["created_at"],
            })
        conn.close()
        return txns
    except Exception:
        conn.close()
        return []


def get_live_financials() -> dict:
    """Read financial state from the engine's KV store and spend tracking."""
    conn = get_engine_db()
    if not conn:
        return {}
    try:
        result = {}

        # Read key financial metrics from KV store
        for key in ["last_known_balance", "last_known_usdc", "total_revenue",
                     "funding_notice_low", "funding_notice_critical"]:
            cursor = conn.execute("SELECT value FROM kv WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                result[key] = row[0]

        # Get inference costs
        cursor = conn.execute("""
            SELECT SUM(cost_cents) as total_cost, COUNT(*) as total_calls
            FROM inference_costs
        """)
        row = cursor.fetchone()
        if row:
            result["total_inference_cost_cents"] = row["total_cost"] or 0
            result["total_inference_calls"] = row["total_calls"] or 0

        # Get spend by category
        cursor = conn.execute("""
            SELECT category, SUM(amount_cents) as total
            FROM spend_tracking
            GROUP BY category
        """)
        spend_by_category = {}
        for row in cursor.fetchall():
            spend_by_category[row["category"]] = row["total"]
        result["spend_by_category"] = spend_by_category

        conn.close()
        return result
    except Exception:
        conn.close()
        return {}


def get_live_heartbeat_history(limit: int = 20) -> list:
    """Read heartbeat task execution history."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT id, task_name, started_at, completed_at, result,
                   duration_ms, error
            FROM heartbeat_history
            ORDER BY started_at DESC LIMIT ?
        """, (limit,))
        history = []
        for row in cursor.fetchall():
            history.append({
                "id": row["id"],
                "task": row["task_name"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "result": row["result"],
                "duration_ms": row["duration_ms"],
                "error": row["error"],
            })
        conn.close()
        return history
    except Exception:
        conn.close()
        return []


def get_live_memory_facts() -> list:
    """Read semantic memory facts — includes portfolio data, financial facts, etc."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT id, category, key, value, confidence, source, created_at, updated_at
            FROM semantic_memory
            ORDER BY updated_at DESC LIMIT 100
        """)
        facts = []
        for row in cursor.fetchall():
            facts.append({
                "id": row["id"],
                "category": row["category"],
                "key": row["key"],
                "value": row["value"],
                "confidence": row["confidence"],
                "source": row["source"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        conn.close()
        return facts
    except Exception:
        conn.close()
        return []


def get_live_soul() -> Optional[str]:
    """Read the current SOUL.md content."""
    soul_path = os.path.expanduser("~/.anima/SOUL.md")
    if os.path.exists(soul_path):
        with open(soul_path, "r") as f:
            return f.read()
    return None



def get_live_turns(limit: int = 50) -> list:
    """Read full agent turns — thinking, tool calls, tokens, cost, state."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT id, timestamp, state, input, thinking, token_usage, cost_cents
            FROM turns ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        turns = []
        for row in cursor.fetchall():
            turn_id = row["id"]
            thinking = row["thinking"] or ""
            token_usage = {}
            try:
                token_usage = json.loads(row["token_usage"]) if row["token_usage"] else {}
            except Exception:
                pass

            # Get tool calls for this turn
            tc_cursor = conn.execute("""
                SELECT id, name, arguments, result, duration_ms, error
                FROM tool_calls WHERE turn_id = ? ORDER BY rowid ASC
            """, (turn_id,))
            tool_calls = []
            for tc in tc_cursor.fetchall():
                args = {}
                try:
                    args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except Exception:
                    pass
                tool_calls.append({
                    "id": tc["id"],
                    "tool": tc["name"],
                    "arguments": args,
                    "result": tc["result"] or "",
                    "duration_ms": tc["duration_ms"],
                    "error": tc["error"],
                })

            turns.append({
                "turn_id": turn_id,
                "timestamp": row["timestamp"],
                "state": row["state"],
                "input": row["input"],
                "thinking": thinking,
                "tool_calls": tool_calls,
                "token_usage": token_usage,
                "cost_cents": row["cost_cents"] or 0,
            })
        conn.close()
        return turns
    except Exception:
        conn.close()
        return []


def get_live_modifications(limit: int = 30) -> list:
    """Read self-modification audit trail."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT id, timestamp, type, description, file_path, diff, reversible
            FROM modifications ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        mods = []
        for row in cursor.fetchall():
            mods.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "type": row["type"],
                "description": row["description"],
                "file_path": row["file_path"],
                "diff": (row["diff"] or "")[:500],
                "reversible": bool(row["reversible"]),
            })
        conn.close()
        return mods
    except Exception:
        conn.close()
        return []



def get_live_identity() -> dict:
    """Read the agent's identity — name, address, state, and any services it has deployed."""
    conn = get_engine_db()
    result = {"name": None, "address": None, "sandbox": None, "services": []}

    # Read from config file (the AI may have changed its name)
    config_path = os.path.expanduser("~/.anima/anima.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                result["name"] = config.get("name")
                result["address"] = config.get("walletAddress")
                result["sandbox"] = config.get("sandboxId")
        except Exception:
            pass

    if not conn:
        return result

    try:
        # Read identity KV pairs
        cursor = conn.execute("SELECT key, value FROM identity")
        for row in cursor.fetchall():
            if row["key"] == "name":
                result["name"] = row["value"]
            elif row["key"] == "address":
                result["address"] = row["value"]
            elif row["key"] == "sandbox":
                result["sandbox"] = row["value"]

        # Read any exposed ports (services the AI has deployed)
        # The AI uses expose_port tool which gets logged in tool_calls
        cursor = conn.execute("""
            SELECT tc.arguments, tc.result, t.timestamp
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            WHERE tc.name IN ('expose_port', 'register_domain', 'create_sandbox')
            ORDER BY t.timestamp DESC LIMIT 50
        """)
        for row in cursor.fetchall():
            args = {}
            result_text = row["result"] or ""
            try:
                args = json.loads(row["arguments"]) if row["arguments"] else {}
            except Exception:
                pass
            result["services"].append({
                "tool": row["arguments"],
                "result": result_text[:500],
                "timestamp": row["timestamp"],
                "args": args,
            })

        # Read any domains registered
        cursor = conn.execute("""
            SELECT tc.arguments, tc.result, t.timestamp
            FROM tool_calls tc
            JOIN turns t ON tc.turn_id = t.id
            WHERE tc.name = 'register_domain'
            ORDER BY t.timestamp DESC LIMIT 10
        """)
        domains = []
        for row in cursor.fetchall():
            try:
                args = json.loads(row["arguments"]) if row["arguments"] else {}
                domains.append({"domain": args.get("domain", ""), "timestamp": row["timestamp"]})
            except Exception:
                pass
        result["domains"] = domains

        # Read installed tools (the AI may have installed MCP servers, npm packages)
        cursor = conn.execute("SELECT id, name, type, config, installed_at, enabled FROM installed_tools ORDER BY installed_at DESC")
        tools = []
        for row in cursor.fetchall():
            tools.append({
                "id": row["id"], "name": row["name"], "type": row["type"],
                "enabled": bool(row["enabled"]), "installed_at": row["installed_at"],
            })
        result["installed_tools"] = tools

        # Read children sandboxes (each is a service the AI deployed)
        cursor = conn.execute("SELECT id, name, sandbox_id, status, created_at FROM children ORDER BY created_at DESC")
        children = []
        for row in cursor.fetchall():
            children.append({
                "id": row["id"], "name": row["name"], "sandbox_id": row["sandbox_id"],
                "status": row["status"], "created_at": row["created_at"],
            })
        result["children_sandboxes"] = children

        conn.close()
    except Exception:
        if conn:
            conn.close()

    return result


def get_live_inbox_messages(limit: int = 50) -> list:
    """Read social messages — interactions with hired/external agents."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT id, from_address, to_address, content, received_at, processed_at, reply_to, status
            FROM inbox_messages ORDER BY received_at DESC LIMIT ?
        """, (limit,))
        msgs = []
        for row in cursor.fetchall():
            msgs.append({
                "id": row["id"],
                "from_address": row["from_address"],
                "to_address": row["to_address"],
                "content": (row["content"] or "")[:1000],
                "signed_at": row["received_at"],
                "created_at": row["received_at"],
                "reply_to": row["reply_to"],
                "status": row["status"],
            })
        conn.close()
        return msgs
    except Exception:
        conn.close()
        return []


def get_live_relationships() -> list:
    """Read relationship memory — trust scores and interaction history with other agents."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT id, entity_address, entity_name, relationship_type,
                   trust_score, interaction_count, last_interaction_at, notes,
                   created_at, updated_at
            FROM relationship_memory ORDER BY updated_at DESC
        """)
        rels = []
        for row in cursor.fetchall():
            rels.append({
                "id": row["id"],
                "address": row["entity_address"],
                "name": row["entity_name"],
                "relationship_type": row["relationship_type"],
                "trust_score": row["trust_score"],
                "interaction_count": row["interaction_count"],
                "last_interaction": row["last_interaction_at"],
                "notes": row["notes"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        conn.close()
        return rels
    except Exception:
        conn.close()
        return []


def get_live_reputation(address: str = None) -> list:
    """Read on-chain reputation scores given/received."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        query = "SELECT id, from_agent, to_agent, score, comment, tx_hash, created_at FROM reputation"
        params = ()
        if address:
            query += " WHERE from_agent = ? OR to_agent = ?"
            params = (address, address)
        query += " ORDER BY created_at DESC LIMIT 50"
        cursor = conn.execute(query, params)
        reps = []
        for row in cursor.fetchall():
            reps.append({
                "id": row["id"],
                "from_agent": row["from_agent"],
                "to_agent": row["to_agent"],
                "score": row["score"],
                "comment": row["comment"],
                "tx_hash": row["tx_hash"],
                "timestamp": row["created_at"],
            })
        conn.close()
        return reps
    except Exception:
        conn.close()
        return []


def get_live_discovered_agents() -> list:
    """Read agents discovered via ERC-8004 registry — these are potential hires."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("""
            SELECT agent_address, agent_card, fetched_from, card_hash,
                   fetch_count, last_fetched_at, created_at
            FROM discovered_agents_cache ORDER BY last_fetched_at DESC
        """)
        agents = []
        for row in cursor.fetchall():
            card = {}
            try:
                card = json.loads(row["agent_card"]) if row["agent_card"] else {}
            except Exception:
                pass
            agents.append({
                "address": row["agent_address"],
                "card": card,
                "name": card.get("name", row["agent_address"][:10] + "..."),
                "description": card.get("description", ""),
                "services": card.get("services", []),
                "fetched_from": row["fetched_from"],
                "fetch_count": row["fetch_count"],
                "last_fetched": row["last_fetched_at"],
                "discovered_at": row["created_at"],
            })
        conn.close()
        return agents
    except Exception:
        conn.close()
        return []


def get_child_lifecycle_events(child_id: str = None, limit: int = 50) -> list:
    """Read child lifecycle state transitions."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        query = "SELECT id, child_id, from_state, to_state, reason, metadata, created_at FROM child_lifecycle_events"
        params = ()
        if child_id:
            query += " WHERE child_id = ?"
            params = (child_id,)
        query += " ORDER BY created_at DESC LIMIT ?"
        params = params + (limit,)
        cursor = conn.execute(query, params)
        events = []
        for row in cursor.fetchall():
            meta = {}
            try:
                meta = json.loads(row["metadata"]) if row["metadata"] else {}
            except Exception:
                pass
            events.append({
                "id": row["id"],
                "child_id": row["child_id"],
                "from_state": row["from_state"],
                "to_state": row["to_state"],
                "reason": row["reason"],
                "metadata": meta,
                "created_at": row["created_at"],
            })
        conn.close()
        return events
    except Exception:
        conn.close()
        return []


# ═══════════════════════════════════════════════════════════
# MISSING TABLE READERS — Complete visibility
# ═══════════════════════════════════════════════════════════

def get_live_working_memory() -> list:
    """Current session goals, plans, active context."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, content_type, content, priority, created_at, expires_at FROM working_memory ORDER BY priority DESC, created_at DESC LIMIT 50")
        items = [{"id": r["id"], "type": r["content_type"], "content": r["content"], "priority": r["priority"], "created_at": r["created_at"], "expires_at": r["expires_at"]} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_episodic_memory(limit: int = 50) -> list:
    """Event log — what happened, when, importance score."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, event_type, summary, importance, classification, created_at FROM episodic_memory ORDER BY created_at DESC LIMIT ?", (limit,))
        items = [{"id": r["id"], "event": r["event_type"], "importance": r["importance"], "valence": r["classification"], "context": r["summary"], "timestamp": r["created_at"]} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_procedural_memory() -> list:
    """Procedures the agent has developed — named step-by-step methods with success tracking."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, name, description, steps, success_count, failure_count, last_used_at, created_at FROM procedural_memory ORDER BY last_used_at DESC LIMIT 50")
        items = [{"id": r["id"], "name": r["name"], "steps": r["steps"], "triggers": r["description"], "success_count": r["success_count"], "failure_count": r["failure_count"], "last_used": r["last_used_at"], "created_at": r["created_at"]} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_installed_tools() -> list:
    """Tools the agent has installed — npm packages, MCP servers."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, name, type, config, installed_at, enabled FROM installed_tools ORDER BY installed_at DESC")
        items = [{"id": r["id"], "name": r["name"], "type": r["type"], "config": r["config"], "installed_at": r["installed_at"], "enabled": bool(r["enabled"])} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_skills() -> list:
    """Skills installed in the agent."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT name, description, enabled, installed_at FROM skills ORDER BY installed_at DESC")
        items = [{"name": r["name"], "description": r["description"], "enabled": bool(r["enabled"]), "installed_at": r["installed_at"]} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_metric_snapshots(limit: int = 50) -> list:
    """Periodic metric captures — performance tracking."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, snapshot_at, metrics_json, created_at FROM metric_snapshots ORDER BY created_at DESC LIMIT ?", (limit,))
        items = []
        for r in cursor.fetchall():
            values = {}
            try: values = json.loads(r["metrics_json"]) if r["metrics_json"] else {}
            except: pass
            items.append({"id": r["id"], "metric": "snapshot", "values": values, "timestamp": r["snapshot_at"]})
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_policy_decisions(limit: int = 50) -> list:
    """Policy engine decisions — what was allowed/denied and why."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, tool_name, decision, reason, risk_level, created_at FROM policy_decisions ORDER BY created_at DESC LIMIT ?", (limit,))
        items = [{"id": r["id"], "tool": r["tool_name"], "decision": r["decision"], "reason": r["reason"], "category": r["risk_level"], "timestamp": r["created_at"]} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_soul_history() -> list:
    """SOUL.md version history — how the agent's identity evolved."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, content, version, change_source, change_reason, created_at FROM soul_history ORDER BY created_at DESC LIMIT 20")
        items = [{"id": r["id"], "content_length": len(r["content"] or ""), "alignment": r["change_reason"], "version": r["version"], "created_at": r["created_at"]} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_onchain_transactions(limit: int = 50) -> list:
    """On-chain USDC transactions — real blockchain payments."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, tx_hash, chain, operation, status, gas_used, metadata, created_at FROM onchain_transactions ORDER BY created_at DESC LIMIT ?", (limit,))
        items = [{"id": r["id"], "type": r["operation"], "tx_hash": r["tx_hash"], "chain": r["chain"], "status": r["status"], "timestamp": r["created_at"]} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_session_summaries(limit: int = 20) -> list:
    """Session summaries — what the agent accomplished in each session."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, summary, turn_count, total_tokens, total_cost_cents, created_at FROM session_summaries ORDER BY created_at DESC LIMIT ?", (limit,))
        items = [{"id": r["id"], "summary": r["summary"], "turns": r["turn_count"], "tool_calls": 0, "cost_cents": r["total_cost_cents"], "started_at": r["created_at"], "ended_at": r["created_at"]} for r in cursor.fetchall()]
        conn.close()
        return items
    except Exception:
        conn.close()
        return []



def get_live_kv_store() -> list:
    """Key-value store — agent's runtime state."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT key, value FROM kv ORDER BY key ASC")
        items = []
        for r in cursor.fetchall():
            val = r["value"]
            parsed = val
            try:
                parsed = json.loads(val) if val else val
            except Exception:
                pass
            items.append({"key": r["key"], "value": parsed, "raw": val})
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_wake_events(limit: int = 20) -> list:
    """Wake events — what triggered the agent to wake up."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT id, source, reason, payload, created_at FROM wake_events ORDER BY created_at DESC LIMIT ?", (limit,))
        items = []
        for r in cursor.fetchall():
            meta = {}
            try:
                meta = json.loads(r["payload"]) if r["payload"] else {}
            except Exception:
                pass
            items.append({"id": r["id"], "source": r["source"], "reason": r["reason"], "metadata": meta, "created_at": r["created_at"]})
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_heartbeat_schedule() -> list:
    """Heartbeat schedule — recurring tasks configuration."""
    conn = get_engine_db()
    if not conn: return []
    try:
        cursor = conn.execute("SELECT task_name, cron_expression, interval_ms, enabled, run_count, last_result, last_run_at, next_run_at FROM heartbeat_schedule ORDER BY task_name ASC")
        items = []
        for r in cursor.fetchall():
            items.append({
                "task": r["task_name"],
                "cron": r["cron_expression"],
                "interval_seconds": (r["interval_ms"] or 0) // 1000 if r["interval_ms"] else None,
                "enabled": bool(r["enabled"]),
                "run_count": r["run_count"],
                "last_result": r["last_result"],
                "last_run_at": r["last_run_at"],
                "next_run_at": r["next_run_at"],
            })
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_skills_full() -> list:
    """All skills from the engine's DB only — no hardcoded lists. Only real data."""
    conn = get_engine_db()
    if not conn:
        return []

    try:
        # 1. Skills from the engine's skills table (these are real, installed skills)
        cursor = conn.execute("SELECT name, description, source, enabled, installed_at, auto_activate FROM skills ORDER BY name")
        items = []
        for r in cursor.fetchall():
            src = r["source"] or "builtin"
            if "openclaw" in src.lower() or "open_claw" in src.lower():
                source_label = "openclaw"
            elif "mcp" in src.lower():
                source_label = "mcp"
            elif src in ("builtin", "genesis", "local"):
                source_label = "anima"
            else:
                source_label = src

            name = r["name"]
            if any(k in name for k in ["deal", "pitch", "scout", "inbound", "outbound"]):
                cat = "deal-flow"
            elif any(k in name for k in ["incubat", "portfolio", "kpi", "exit"]):
                cat = "portfolio"
            elif any(k in name for k in ["capital", "budget", "financ", "treasury", "roi", "lp"]):
                cat = "finance"
            elif any(k in name for k in ["hiring", "talent", "hr", "dei", "agent-sust"]):
                cat = "talent"
            elif any(k in name for k in ["compliance", "ethics", "scam", "cost-valid"]):
                cat = "compliance"
            elif any(k in name for k in ["market", "customer", "crm", "event"]):
                cat = "growth"
            elif any(k in name for k in ["conway", "tool", "skill", "admin", "operational", "survival", "strategy"]):
                cat = "operations"
            elif any(k in name for k in ["technical", "m-a", "syndic", "term-sheet", "legal"]):
                cat = "advisory"
            else:
                cat = "general"

            items.append({
                "name": name,
                "description": r["description"],
                "source": source_label,
                "category": cat,
                "enabled": bool(r["enabled"]),
                "installed_at": r["installed_at"],
                "auto_activate": bool(r["auto_activate"]) if r["auto_activate"] is not None else False,
                "used_by": ["founder"],
                "use_count": 0,
            })

        # 2. Installed tools (MCP servers, OpenClaw, npm packages — only real installed ones)
        cursor = conn.execute("SELECT id, name, type, config, installed_at, enabled FROM installed_tools ORDER BY installed_at DESC")
        for r in cursor.fetchall():
            tool_type = (r["type"] or "").lower()
            if "mcp" in tool_type:
                source_label = "mcp"
            elif "claw" in tool_type:
                source_label = "openclaw"
            else:
                source_label = "installed"

            items.append({
                "name": r["name"],
                "description": f"{r['type']}: {r['name']}",
                "source": source_label,
                "category": "tools",
                "enabled": bool(r["enabled"]),
                "installed_at": r["installed_at"],
                "auto_activate": False,
                "used_by": ["founder"],
                "use_count": 0,
            })

        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_models() -> list:
    """AI models available to the agent."""
    conn = get_engine_db()
    if not conn:
        return []
    try:
        cursor = conn.execute("SELECT model_id, provider, display_name, tier_minimum, cost_per_1k_input, cost_per_1k_output, max_tokens, context_window, supports_tools, supports_vision, enabled FROM model_registry ORDER BY cost_per_1k_input ASC")
        items = []
        for r in cursor.fetchall():
            items.append({
                "id": r["model_id"],
                "provider": r["provider"],
                "name": r["display_name"],
                "tier": r["tier_minimum"],
                "cost_input": r["cost_per_1k_input"],
                "cost_output": r["cost_per_1k_output"],
                "max_tokens": r["max_tokens"],
                "context_window": r["context_window"],
                "tools": bool(r["supports_tools"]),
                "vision": bool(r["supports_vision"]),
                "enabled": bool(r["enabled"]),
            })
        conn.close()
        return items
    except Exception:
        conn.close()
        return []


def get_live_tool_usage() -> dict:
    """Aggregated tool usage stats from tool_calls table."""
    conn = get_engine_db()
    if not conn:
        return {}
    try:
        cursor = conn.execute("""
            SELECT name, COUNT(*) as count, AVG(duration_ms) as avg_ms,
                   SUM(CASE WHEN error IS NOT NULL AND error != '' THEN 1 ELSE 0 END) as errors
            FROM tool_calls GROUP BY name ORDER BY count DESC
        """)
        usage = {}
        for r in cursor.fetchall():
            usage[r["name"]] = {
                "count": r["count"],
                "avg_ms": round(r["avg_ms"] or 0),
                "errors": r["errors"],
            }
        conn.close()
        return usage
    except Exception:
        conn.close()
        return {}
