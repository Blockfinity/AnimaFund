"""
PLATFORM: Conway API integration — real-time data from api.conway.tech.
"""
import os
import aiohttp
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["conway"])

CONWAY_API = os.environ.get("CONWAY_API", "https://api.conway.tech")
CONWAY_DOMAINS_API = os.environ.get("CONWAY_DOMAINS_API", "https://api.conway.domains")
CONWAY_INFERENCE_API = os.environ.get("CONWAY_INFERENCE", "https://inference.conway.tech")


async def _get_conway_api_key() -> str:
    from agent_state import get_conway_api_key
    return await get_conway_api_key()


@router.get("/conway/balance")
async def get_conway_balance():
    """Real-time balance from Conway API."""
    api_key = await _get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured", "source": "conway_api"}

    result = {"source": "conway_api"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{CONWAY_API}/v1/credits/balance",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result["credits_cents"] = data.get("credits_cents", 0)
                    result["credits_usd"] = data.get("credits_cents", 0) / 100
        except Exception:
            result["credits_error"] = "Failed to fetch credits"

        try:
            async with session.get(
                f"{CONWAY_API}/v1/sandboxes",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result["sandboxes"] = data.get("sandboxes", [])
                    result["sandbox_count"] = data.get("count", 0)
        except Exception:
            result["sandbox_error"] = "Failed to fetch sandboxes"

    return result


@router.get("/conway/sandboxes")
async def get_conway_sandboxes():
    """List sandboxes from Conway Cloud API."""
    api_key = await _get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{CONWAY_API}/v1/sandboxes",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"Conway API returned {resp.status}"}
        except Exception as e:
            return {"error": str(e)}


@router.get("/conway/credits/pricing")
async def get_conway_pricing():
    """Get Conway credits pricing tiers."""
    api_key = await _get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{CONWAY_API}/v1/credits/pricing",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"Conway API returned {resp.status}"}
        except Exception as e:
            return {"error": str(e)}


@router.get("/conway/credits/history")
async def get_conway_credits_history():
    """Get Conway credits transaction history."""
    api_key = await _get_conway_api_key()
    if not api_key:
        return {"error": "No Conway API key configured"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{CONWAY_API}/v1/credits/history",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"Conway API returned {resp.status}"}
        except Exception as e:
            return {"error": str(e)}


@router.get("/conway/domains/search")
async def search_conway_domains(q: str = "animafund", tlds: str = "ai,com,io,xyz"):
    """Search available domains via Conway Domains API."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{CONWAY_DOMAINS_API}/domains/search?q={q}&tlds={tlds}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"Conway Domains API returned {resp.status}"}
        except Exception as e:
            return {"error": str(e)}


@router.get("/conway/inference/health")
async def check_conway_inference():
    """Check Conway inference API health."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{CONWAY_INFERENCE_API}/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"status": "error", "code": resp.status}
        except Exception as e:
            return {"status": "error", "detail": str(e)}


@router.get("/conway/health")
async def check_conway_apis():
    """Check health of all Conway API services."""
    results = {}
    async with aiohttp.ClientSession() as session:
        for name, url in [
            ("cloud", f"{CONWAY_API}/health"),
            ("domains", f"{CONWAY_DOMAINS_API}/health"),
            ("inference", f"{CONWAY_INFERENCE_API}/health"),
        ]:
            try:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    results[name] = {
                        "status": "healthy" if resp.status == 200 else "error",
                        "code": resp.status,
                    }
            except Exception as e:
                results[name] = {"status": "unreachable", "detail": str(e)}

    all_healthy = all(r["status"] == "healthy" for r in results.values())
    return {"all_healthy": all_healthy, "services": results}
