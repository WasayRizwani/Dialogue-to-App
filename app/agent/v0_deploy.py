"""
Stage 7: Send the rendered prompt to the v0.dev API and return the chat URL.

v0 API reference: https://v0.dev/docs/api
Auth token:       https://v0.dev/settings/api-keys
"""
from __future__ import annotations

import httpx

from app.core.settings import settings

_V0_API_BASE = "https://v0.dev/api/v1"


async def v0_deploy(prompt: str) -> str:
    """POST prompt to v0, return the URL of the generated chat (e.g. https://v0.dev/chat/xxxxx)."""
    if not settings.v0_api_token:
        raise ValueError(
            "V0_API_TOKEN is not set. Add it to your .env file — "
            "get a token at https://v0.dev/settings/api-keys"
        )

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{_V0_API_BASE}/chats",
            headers={
                "Authorization": f"Bearer {settings.v0_api_token}",
                "Content-Type": "application/json",
            },
            json={"messages": [{"role": "user", "content": prompt}]},
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"v0 API returned {exc.response.status_code}: {exc.response.text}"
        ) from exc

    data = response.json()

    # v0 returns the shareable URL under the "url" key
    url = data.get("url") or data.get("demo_url") or data.get("chat", {}).get("url")
    if not url:
        raise RuntimeError(f"v0 API response missing URL field. Full response: {data}")

    return url
