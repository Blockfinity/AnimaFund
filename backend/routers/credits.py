"""
PLATFORM: Conway Credits — funding mechanism for agent sandbox compute.
Uses Conway's x402 payment protocol. All state in MongoDB.
"""
import io
import base64
import aiohttp
import qrcode
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel

from database import get_db
from config import CONWAY_API
from agent_state import get_active_agent_id, get_conway_api_key, set_conway_api_key

router = APIRouter(prefix="/api/credits", tags=["credits"])


class SetKeyRequest(BaseModel):
    api_key: str


@router.post("/set-key")
async def set_conway_api_key_endpoint(req: SetKeyRequest):
    """Accept a Conway API key, validate against Conway API, persist to MongoDB."""
    key = req.api_key.strip()
    if not key or not key.startswith("cnwy_"):
        return {"success": False, "error": "Invalid key format. Conway keys start with 'cnwy_'"}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        try:
            async with session.get(
                f"{CONWAY_API}/v1/credits/balance",
                headers={"Authorization": f"Bearer {key}"},
            ) as resp:
                if resp.status == 401:
                    return {"success": False, "error": "Invalid API key — Conway rejected it"}
                if resp.status == 200:
                    data = await resp.json()
                    credits_cents = data.get("credits_cents", 0)
                else:
                    return {"success": False, "error": f"Conway returned status {resp.status}"}
        except Exception as e:
            return {"success": False, "error": f"Could not reach Conway API: {e}"}

    # Key valid — persist to MongoDB via agent_state
    await set_conway_api_key(key)

    return {
        "success": True,
        "credits_cents": credits_cents,
        "credits_usd": credits_cents / 100,
        "message": f"Conway API key saved. Balance: ${credits_cents / 100:.2f}",
        "key_prefix": key[:12] + "...",
    }


@router.get("/key-status")
async def conway_key_status():
    """Check if a Conway API key is configured and valid."""
    key = await get_conway_api_key()
    if not key:
        return {"configured": False, "message": "No Conway API key set. Paste your key from Conway."}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
        try:
            async with session.get(
                f"{CONWAY_API}/v1/credits/balance",
                headers={"Authorization": f"Bearer {key}"},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "configured": True,
                        "valid": True,
                        "key_prefix": key[:12] + "...",
                        "credits_cents": data.get("credits_cents", 0),
                    }
                return {"configured": True, "valid": False, "error": f"Conway returned {resp.status}"}
        except Exception:
            return {"configured": True, "valid": False, "error": "Cannot reach Conway API"}


async def _conway_get(path: str) -> dict:
    api_key = await get_conway_api_key()
    if not api_key:
        return {"error": "No CONWAY_API_KEY configured"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        try:
            async with session.get(
                f"{CONWAY_API}{path}",
                headers={"Authorization": f"Bearer {api_key}"},
            ) as resp:
                return await resp.json()
        except Exception as e:
            return {"error": str(e)}


async def _conway_post_raw(path: str, body: dict) -> tuple:
    api_key = await get_conway_api_key()
    if not api_key:
        return (0, {"error": "No CONWAY_API_KEY configured"})
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        try:
            async with session.post(
                f"{CONWAY_API}{path}",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=body,
            ) as resp:
                data = await resp.json()
                return (resp.status, data)
        except Exception as e:
            return (0, {"error": str(e)})


def _generate_qr_base64(data: str) -> str:
    try:
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
    except Exception:
        return ""


@router.get("/balance")
async def get_credits_balance():
    data = await _conway_get("/v1/credits/balance")
    if "error" in data:
        return {"credits_cents": 0, "credits_usd": 0.0, "error": data["error"]}
    credits_cents = data.get("credits_cents", 0)
    return {"credits_cents": credits_cents, "credits_usd": credits_cents / 100, "raw": data}


@router.get("/pricing")
async def get_credits_pricing():
    data = await _conway_get("/v1/credits/pricing")
    if "error" in data:
        return {"error": data["error"]}
    return data


class PurchaseRequest(BaseModel):
    amount: int = 25


@router.post("/purchase")
async def purchase_credits(req: PurchaseRequest):
    pre_balance = await _conway_get("/v1/credits/balance")
    pre_credits = pre_balance.get("credits_cents", 0) if "error" not in pre_balance else 0

    status_code, data = await _conway_post_raw("/v1/credits/purchase", {"amount": req.amount})

    if status_code == 0:
        return {"success": False, "error": data.get("error", "Request failed")}

    if status_code == 402 and "accepts" in data:
        payment = data["accepts"][0]
        pay_to = payment.get("payTo", "")
        amount_raw = payment.get("maxAmountRequired", "0")
        amount_usdc = int(amount_raw) / 1e6

        eip681_uri = f"ethereum:{pay_to}@8453/transfer?address={payment.get('asset', '')}&uint256={amount_raw}"
        qr_code = _generate_qr_base64(pay_to)
        qr_code_eip681 = _generate_qr_base64(eip681_uri)

        try:
            db = get_db()
            await db.credit_purchases.insert_one({
                "type": "purchase_initiated",
                "amount_usd": req.amount,
                "amount_usdc": amount_usdc,
                "pay_to": pay_to,
                "pre_balance_cents": pre_credits,
                "status": "pending_payment",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass

        return {
            "success": True,
            "payment_required": True,
            "pay_to": pay_to,
            "amount_usdc": amount_usdc,
            "amount_raw": amount_raw,
            "amount_usd": req.amount,
            "network": "Base (EIP-155:8453)",
            "asset": "USDC",
            "asset_contract": payment.get("asset", ""),
            "description": payment.get("description", ""),
            "resource": payment.get("resource", ""),
            "qr_code": qr_code,
            "qr_code_eip681": qr_code_eip681,
            "pre_balance_cents": pre_credits,
            "instructions": [
                f"Send exactly {amount_usdc} USDC on Base network",
                f"To address: {pay_to}",
                "Use any wallet that supports Base (Coinbase Wallet, MetaMask, etc.)",
                "Credits will be added automatically after confirmation",
                "Use /api/credits/verify to confirm credits were received",
            ],
        }

    return {"success": False, "status_code": status_code, "error": data.get("error", data.get("message", "Unexpected response")), "raw": data}


@router.post("/verify")
async def verify_credits():
    balance_data = await _conway_get("/v1/credits/balance")
    if "error" in balance_data:
        return {"verified": False, "error": balance_data["error"]}

    current_cents = balance_data.get("credits_cents", 0)

    try:
        db = get_db()
        await db.credit_verifications.insert_one({
            "type": "balance_verification",
            "credits_cents": current_cents,
            "credits_usd": current_cents / 100,
            "raw_response": {k: v for k, v in balance_data.items() if k != "_id"},
            "verified_at": datetime.now(timezone.utc).isoformat(),
        })

        last_purchase = await db.credit_purchases.find_one(
            {"status": "pending_payment"},
            sort=[("created_at", -1)],
        )
        if last_purchase and current_cents > last_purchase.get("pre_balance_cents", 0):
            gained = current_cents - last_purchase["pre_balance_cents"]
            await db.credit_purchases.update_one(
                {"_id": last_purchase["_id"]},
                {"$set": {
                    "status": "confirmed",
                    "post_balance_cents": current_cents,
                    "credits_gained_cents": gained,
                    "confirmed_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            return {"verified": True, "credits_cents": current_cents, "credits_usd": current_cents / 100,
                    "credits_gained_cents": gained, "message": f"Payment confirmed! {gained / 100:.2f} USD in credits received."}
    except Exception:
        pass

    return {"verified": True, "credits_cents": current_cents, "credits_usd": current_cents / 100, "message": "Balance checked successfully."}


@router.get("/history")
async def credit_purchase_history():
    try:
        db = get_db()
        purchases = await db.credit_purchases.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
        verifications = await db.credit_verifications.find({}, {"_id": 0}).sort("verified_at", -1).limit(20).to_list(20)
        return {"purchases": purchases, "verifications": verifications}
    except Exception as e:
        return {"purchases": [], "verifications": [], "error": str(e)}
