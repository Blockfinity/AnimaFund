"""
Conway Credits — funding mechanism for sandbox compute.
Uses Conway's x402 payment protocol to generate payment instructions.
"""
import os
import io
import base64
import aiohttp
import qrcode
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/credits", tags=["credits"])

CONWAY_API = "https://api.conway.tech"


def _get_conway_api_key() -> str:
    return os.environ.get("CONWAY_API_KEY", "")


async def _conway_get(path: str) -> dict:
    api_key = _get_conway_api_key()
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
    """POST to Conway API and return (status_code, response_body)."""
    api_key = _get_conway_api_key()
    if not api_key:
        return (0, {"error": "No CONWAY_API_KEY configured"})
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        try:
            async with session.post(
                f"{CONWAY_API}{path}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            ) as resp:
                data = await resp.json()
                return (resp.status, data)
        except Exception as e:
            return (0, {"error": str(e)})


def _generate_qr_base64(data: str) -> str:
    """Generate a QR code as base64 data URI."""
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
    """Fetch current Conway API key credit balance."""
    data = await _conway_get("/v1/credits/balance")
    if "error" in data:
        return {"credits_cents": 0, "credits_usd": 0.0, "error": data["error"]}
    credits_cents = data.get("credits_cents", 0)
    return {
        "credits_cents": credits_cents,
        "credits_usd": credits_cents / 100,
        "raw": data,
    }


@router.get("/pricing")
async def get_credits_pricing():
    """Fetch Conway credit pricing tiers and VM costs."""
    data = await _conway_get("/v1/credits/pricing")
    if "error" in data:
        return {"error": data["error"]}
    return data


class PurchaseRequest(BaseModel):
    amount: int = 25  # USD amount — must match a tier: 5, 25, 100, 500, 1000, 2500


@router.post("/purchase")
async def purchase_credits(req: PurchaseRequest):
    """Call Conway's x402 purchase endpoint to get USDC payment details.
    Returns the payment address, amount, and a QR code for the user."""
    status_code, data = await _conway_post_raw("/v1/credits/purchase", {"amount": req.amount})

    if status_code == 0:
        return {"success": False, "error": data.get("error", "Request failed")}

    # x402 returns HTTP 402 with payment instructions
    if status_code == 402 and "accepts" in data:
        payment = data["accepts"][0]
        pay_to = payment.get("payTo", "")
        amount_raw = payment.get("maxAmountRequired", "0")
        amount_usdc = int(amount_raw) / 1e6
        description = payment.get("description", "")

        # Generate QR code for the payTo address
        # Use EIP-681 format for better wallet compatibility on Base
        eip681_uri = f"ethereum:{pay_to}@8453/transfer?address={payment.get('asset', '')}&uint256={amount_raw}"
        qr_code = _generate_qr_base64(pay_to)
        qr_code_eip681 = _generate_qr_base64(eip681_uri)

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
            "description": description,
            "resource": payment.get("resource", ""),
            "qr_code": qr_code,
            "qr_code_eip681": qr_code_eip681,
            "instructions": [
                f"Send exactly {amount_usdc} USDC on Base network",
                f"To address: {pay_to}",
                "Use any wallet that supports Base (Coinbase Wallet, MetaMask, etc.)",
                "Credits will be added automatically after confirmation",
            ],
        }

    # Unexpected response
    return {
        "success": False,
        "status_code": status_code,
        "error": data.get("error", data.get("message", "Unexpected response")),
        "raw": data,
    }
