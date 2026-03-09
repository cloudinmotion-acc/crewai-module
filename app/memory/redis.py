"""Stub representing the runtime's RedisMemory implementation.

In the full `agent-runtime` package this class provides an async
Redis-backed memory store.  Here we define a minimal API so that
imports succeed; most logic is either delegated to the `crew.memory`
module or left unimplemented.
"""

from __future__ import annotations
from typing import Any, Optional


class RedisMemory:
    def __init__(self, host: str, port: int = 6379, password: Optional[str] = None) -> None:
        # This stub doesn't actually connect to anything.  It mimics the
        # constructor signature used by ``crew/agent.py`` so that
        # callers can instantiate it if needed.
        self.host = host
        self.port = port
        self.password = password

    async def set(self, key: str, value: Any) -> None:  # pragma: no cover
        raise NotImplementedError("RedisMemory stub cannot perform operations")

    async def get(self, key: str) -> Any:  # pragma: no cover
        raise NotImplementedError("RedisMemory stub cannot perform operations")

    async def append_to_list(self, key: str, value: Any) -> None:  # pragma: no cover
        raise NotImplementedError("RedisMemory stub cannot perform operations")

    async def get_list(self, key: str) -> list[Any]:  # pragma: no cover
        raise NotImplementedError("RedisMemory stub cannot perform operations")
