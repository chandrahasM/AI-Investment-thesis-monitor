import httpx
from app.core.config import settings

EXA_BASE_URL = "https://api.exa.ai"


def get_exa_headers() -> dict:
    return {
        "x-api-key": settings.EXA_API_KEY,
        "Content-Type": "application/json",
    }


def get_exa_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=EXA_BASE_URL,
        headers=get_exa_headers(),
        timeout=120.0,
    )
