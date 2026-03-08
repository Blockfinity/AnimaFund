"""
Payment Tracker — Monitors agent revenue and enforces the 50% creator payout rule.
Reads from the engine's state.db (transactions, memory facts, on-chain data)
and tracks whether the agent is honoring its payment obligations.
"""

import os
from datetime import datetime, timezone
from engine_bridge import get_engine_db


FUND_LAUNCH_THRESHOLD = 10000  # $10K minimum to launch fund


def get_payment_status():
    """
    Analyze the agent's financial state from real data in state.db.
    Returns a summary of revenue, payouts, compliance, and fund readiness.
    """
    creator_sol = os.environ.get("CREATOR_WALLET", "")
    creator_eth = os.environ.get("CREATOR_ETH_ADDRESS", "")
    conn = get_engine_db()
    if not conn:
        return {
            "engine_running": False,
            "total_revenue": 0,
            "total_sustainability_cost": 0,
            "total_creator_payouts": 0,
            "owed_to_creator": 0,
            "payout_compliant": True,
            "fund_launch_ready": False,
            "fund_launch_threshold": FUND_LAUNCH_THRESHOLD,
            "capital_raised": 0,
            "transactions": [],
            "payout_history": [],
            "creator_wallets": {
                "solana": creator_sol,
                "ethereum": creator_eth,
            },
        }

    try:
        # Revenue events from memory facts
        revenue_facts = []
        payout_facts = []
        sustainability_facts = []

        try:
            cursor = conn.execute(
                "SELECT fact, created_at FROM memory WHERE fact LIKE '%revenue%' OR fact LIKE '%earned%' OR fact LIKE '%income%' OR fact LIKE '%payment received%' ORDER BY created_at DESC"
            )
            revenue_facts = [{"fact": r["fact"], "created_at": r["created_at"]} for r in cursor.fetchall()]
        except Exception:
            pass

        try:
            cursor = conn.execute(
                "SELECT fact, created_at FROM memory WHERE fact LIKE '%creator payout%' OR fact LIKE '%creator payment%' OR fact LIKE '%sent to creator%' OR fact LIKE '%transferred to creator%' ORDER BY created_at DESC"
            )
            payout_facts = [{"fact": r["fact"], "created_at": r["created_at"]} for r in cursor.fetchall()]
        except Exception:
            pass

        try:
            cursor = conn.execute(
                "SELECT fact, created_at FROM memory WHERE fact LIKE '%burn%' OR fact LIKE '%cost%' OR fact LIKE '%expense%' OR fact LIKE '%inference cost%' OR fact LIKE '%compute cost%' ORDER BY created_at DESC"
            )
            sustainability_facts = [{"fact": r["fact"], "created_at": r["created_at"]} for r in cursor.fetchall()]
        except Exception:
            pass

        # On-chain transactions
        onchain_txs = []
        try:
            cursor = conn.execute(
                "SELECT id, type, amount, token, chain, from_address, to_address, tx_hash, status, created_at FROM onchain_transactions ORDER BY created_at DESC LIMIT 50"
            )
            onchain_txs = [dict(r) for r in cursor.fetchall()]
        except Exception:
            pass

        # Financial state from kv store
        total_revenue = 0
        total_costs = 0
        total_payouts = 0
        capital_raised = 0

        try:
            cursor = conn.execute("SELECT key, value FROM kv_store WHERE key LIKE '%revenue%' OR key LIKE '%balance%' OR key LIKE '%capital%' OR key LIKE '%payout%' OR key LIKE '%cost%'")
            for r in cursor.fetchall():
                key = r["key"].lower()
                try:
                    val = float(r["value"])
                except (ValueError, TypeError):
                    continue
                if "revenue" in key or "earned" in key:
                    total_revenue += val
                elif "payout" in key or "creator" in key:
                    total_payouts += val
                elif "cost" in key or "burn" in key or "expense" in key:
                    total_costs += val
                elif "capital" in key or "raised" in key:
                    capital_raised += val
        except Exception:
            pass

        # Calculate what's owed
        net_after_sustainability = max(0, total_revenue - total_costs)
        owed = (net_after_sustainability * 0.50) - total_payouts
        compliant = owed <= 0.01  # Small tolerance for rounding

        conn.close()

        return {
            "engine_running": True,
            "total_revenue": round(total_revenue, 2),
            "total_sustainability_cost": round(total_costs, 2),
            "net_after_sustainability": round(net_after_sustainability, 2),
            "total_creator_payouts": round(total_payouts, 2),
            "owed_to_creator": round(max(0, owed), 2),
            "payout_compliant": compliant,
            "fund_launch_ready": capital_raised >= FUND_LAUNCH_THRESHOLD,
            "fund_launch_threshold": FUND_LAUNCH_THRESHOLD,
            "capital_raised": round(capital_raised, 2),
            "revenue_events_count": len(revenue_facts),
            "payout_events_count": len(payout_facts),
            "onchain_transactions": len(onchain_txs),
            "recent_revenue": revenue_facts[:10],
            "recent_payouts": payout_facts[:10],
            "recent_onchain": onchain_txs[:10],
            "sustainability_events": sustainability_facts[:10],
            "creator_wallets": {
                "solana": creator_sol,
                "ethereum": creator_eth,
            },
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        if conn:
            conn.close()
        return {"error": str(e), "engine_running": False}
