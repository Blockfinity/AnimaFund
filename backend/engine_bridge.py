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
            SELECT id, name, address, sandboxId, genesisPrompt,
                   fundedAmountCents, status, createdAt, lastChecked
            FROM children ORDER BY createdAt DESC
        """)
        agents = []
        for row in cursor.fetchall():
            # Try to extract role from genesis prompt
            prompt = row["genesisPrompt"] or ""
            role = "Agent"
            if "You are" in prompt:
                role_part = prompt.split("You are")[1].split(".")[0].split(",")[0].strip()
                role = role_part[:40]

            agents.append({
                "agent_id": row["id"],
                "name": row["name"],
                "role": role,
                "wallet_address": row["address"],
                "sandbox_id": row["sandboxId"],
                "funded_cents": row["fundedAmountCents"],
                "status": row["status"],
                "created_at": row["createdAt"],
                "last_checked": row["lastChecked"],
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
            SELECT tc.id, tc.turnId, tc.name as tool_name, tc.arguments,
                   tc.result, tc.durationMs, tc.error,
                   t.timestamp, t.state
            FROM tool_calls tc
            JOIN turns t ON tc.turnId = t.id
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
                "turn_id": row["turnId"],
                "tool_name": row["tool_name"],
                "arguments": args,
                "result_preview": (row["result"] or "")[:200],
                "duration_ms": row["durationMs"],
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
            SELECT id, type, amountCents, balanceAfterCents, description, timestamp
            FROM transactions ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        txns = []
        for row in cursor.fetchall():
            txns.append({
                "id": row["id"],
                "type": row["type"],
                "amount_cents": row["amountCents"],
                "balance_after_cents": row["balanceAfterCents"],
                "description": row["description"],
                "timestamp": row["timestamp"],
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
            SELECT SUM(costCents) as total_cost, COUNT(*) as total_calls
            FROM inference_costs
        """)
        row = cursor.fetchone()
        if row:
            result["total_inference_cost_cents"] = row["total_cost"] or 0
            result["total_inference_calls"] = row["total_calls"] or 0

        # Get spend by category
        cursor = conn.execute("""
            SELECT category, SUM(amountCents) as total
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
            SELECT id, taskName, startedAt, completedAt, result,
                   durationMs, error
            FROM heartbeat_history
            ORDER BY startedAt DESC LIMIT ?
        """, (limit,))
        history = []
        for row in cursor.fetchall():
            history.append({
                "id": row["id"],
                "task": row["taskName"],
                "started_at": row["startedAt"],
                "completed_at": row["completedAt"],
                "result": row["result"],
                "duration_ms": row["durationMs"],
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
            SELECT id, category, key, value, confidence, source, createdAt, updatedAt
            FROM semantic_memory
            ORDER BY updatedAt DESC LIMIT 100
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
                "created_at": row["createdAt"],
                "updated_at": row["updatedAt"],
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
            SELECT id, timestamp, state, input, thinking, tokenUsage, costCents
            FROM turns ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        turns = []
        for row in cursor.fetchall():
            turn_id = row["id"]
            thinking = row["thinking"] or ""
            token_usage = {}
            try:
                token_usage = json.loads(row["tokenUsage"]) if row["tokenUsage"] else {}
            except Exception:
                pass

            # Get tool calls for this turn
            tc_cursor = conn.execute("""
                SELECT id, name, arguments, result, durationMs, error
                FROM tool_calls WHERE turnId = ? ORDER BY rowid ASC
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
                    "duration_ms": tc["durationMs"],
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
                "cost_cents": row["costCents"] or 0,
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
            SELECT id, timestamp, type, description, filePath, diff, reversible
            FROM modifications ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        mods = []
        for row in cursor.fetchall():
            mods.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "type": row["type"],
                "description": row["description"],
                "file_path": row["filePath"],
                "diff": (row["diff"] or "")[:500],
                "reversible": bool(row["reversible"]),
            })
        conn.close()
        return mods
    except Exception:
        conn.close()
        return []
