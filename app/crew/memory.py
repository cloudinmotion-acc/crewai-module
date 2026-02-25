"""Memory backend interfaces and helpers for CrewAI.

The agent-runtime package already provides a Redis-based memory engine,
but we define an abstract interface here so the rest of the crew module
can be backend-agnostic.  An in-memory implementation is included for
local testing and CLI replay features.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MemoryBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    async def append_to_list(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    async def get_list(self, key: str) -> List[Any]:
        pass


class InMemoryMemory(MemoryBackend):
    """Simple asyncio-safe in-memory storage for testing/CLI."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        # lists stored separately for convenience
        self._lists: Dict[str, List[Any]] = {}
        # protect with a lock so concurrent coroutines behave
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            return self._store.get(key)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._store[key] = value

    async def append_to_list(self, key: str, value: Any) -> None:
        async with self._lock:
            self._lists.setdefault(key, []).append(value)

    async def get_list(self, key: str) -> List[Any]:
        async with self._lock:
            return list(self._lists.get(key, []))


# wrapper around the runtime's RedisMemory if available
try:
    from app.memory.redis import RedisMemory as _RuntimeRedisMemory

    class RedisMemory(_RuntimeRedisMemory, MemoryBackend):
        # subclass simply to satisfy our type system
        pass
except ImportError:  # pragma: no cover - runtime package not available
    # provide a dummy implementation so imports don't break
    class RedisMemory(MemoryBackend):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("RedisMemory requires the agent-runtime package")

