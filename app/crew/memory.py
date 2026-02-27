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
        # ``asyncio.Lock`` requires a running event loop on Python 3.9,
        # which isn't available during module import or when tests
        # construct the object synchronously.  Lazily create the lock in
        # the first async operation to avoid "no current event loop"
        # errors.
        self._lock = None  # type: ignore[var-annotated]

    async def get(self, key: str) -> Optional[Any]:
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:  # type: ignore
            return self._store.get(key)

    async def set(self, key: str, value: Any) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:  # type: ignore
            self._store[key] = value

    async def append_to_list(self, key: str, value: Any) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:  # type: ignore
            self._lists.setdefault(key, []).append(value)

    async def get_list(self, key: str) -> List[Any]:
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:  # type: ignore
            return list(self._lists.get(key, []))


# real Redis-backed implementation using redis-py
try:
    import redis.asyncio as aioredis
except ImportError:  # redis package not installed (should be in requirements)
    aioredis = None  # type: ignore


class RedisMemory(MemoryBackend):
    """Async Redis-based memory store."""

    def __init__(self, host: str, port: int = 6379, password: Optional[str] = None) -> None:
        if aioredis is None:
            raise RuntimeError("redis package is required for RedisMemory")
        self._client = aioredis.Redis(host=host, port=port, password=password)

    async def get(self, key: str) -> Optional[Any]:
        val = await self._client.get(key)
        if val is None:
            return None
        try:
            return val.decode()  # assume utf-8 string
        except AttributeError:
            return val

    async def set(self, key: str, value: Any) -> None:
        # convert non-bytes to string
        if not isinstance(value, (bytes, bytearray)):
            value = str(value)
        await self._client.set(key, value)

    async def append_to_list(self, key: str, value: Any) -> None:
        if not isinstance(value, (bytes, bytearray)):
            value = str(value)
        await self._client.rpush(key, value)

    async def get_list(self, key: str) -> List[Any]:
        entries = await self._client.lrange(key, 0, -1)
        # decode bytes
        result: List[Any] = []
        for v in entries:
            try:
                result.append(v.decode())
            except AttributeError:
                result.append(v)
        return result

# previous stub for runtime compatibility removed

