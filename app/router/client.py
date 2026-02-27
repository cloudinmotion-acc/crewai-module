"""Simple ModelRouterClient stub for local development.

This client mirrors the minimal initializer used by the real
`ModelRouterClient` in the runtime but does not perform network
requests. It exists so imports succeed and components depending on
the router can be exercised locally.
"""
from __future__ import annotations
from typing import Any, Dict, Optional

import httpx
import logging

logger = logging.getLogger(__name__)


class ModelRouterClient:
    """HTTP client for the model-router service.

    This implementation performs a POST to ``/generate`` on the router and
    returns the model's text output.  The actual API shape is loosely based
    on the router's OpenAPI spec used in the runtime; callers should handle
    whatever JSON fields are returned.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        logger.info(f"ModelRouterClient initialized with URL: {self.base_url}")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-5-nano",
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any] | str:
        """Call the model-router's `/generate` endpoint.

        The router expects JSON with ``prompt``, ``model`` and optionally
        a ``state`` object; it returns a JSON blob containing at least one
        of ``output``, ``response`` or ``text`` and may include an updated
        ``state`` dict.  We return the parsed JSON to the caller so they can
        inspect or persist the state if needed.
        """
        payload: Dict[str, Any] = {"prompt": prompt, "model": model}
        if state is not None:
            payload["state"] = state
        resp = await self._client.post("/generate", json=payload)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:  # not JSON
            # fall back to raw text
            return resp.text
        return data

    async def close(self) -> None:
        await self._client.aclose()

    def __repr__(self) -> str:  # helpful in logs/tests
        return f"ModelRouterClient(base_url={self.base_url!r})"
