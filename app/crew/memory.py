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
import asyncio
import json
import logging
import os
import time
from ssl import create_default_context, CERT_REQUIRED

logger = logging.getLogger(__name__)

try:
    import certifi
    from redis.cluster import RedisCluster
except ImportError:
    certifi = None
    RedisCluster = None

# Session expiration: 24 hours (86400 seconds)
SESSION_TTL = int(os.getenv("SESSION_TTL", "86400"))


class RedisMemory(MemoryBackend):
    """Redis Cluster-based memory store with SSL/TLS support for AWS ElastiCache.
    
    Uses synchronous RedisCluster but wrapped for async compatibility.
    """

    def __init__(
        self, 
        host: str, 
        port: int = 6379, 
        password: Optional[str] = None,
        max_retries: int = 5,
        retry_delay: int = 10
    ) -> None:
        if RedisCluster is None:
            raise RuntimeError("redis[cluster] is required for RedisMemory")
        if not host:
            raise ValueError("REDIS_HOST environment variable is not set")
        
        self.host = host
        self.port = port
        self.password = password
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client = None
        self._initialized = False
        self._loop = None
        
    async def _ensure_connected(self) -> None:
        """Connect to Redis Cluster with retry logic and SSL/TLS support."""
        if self._initialized and self._client:
            return
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Attempting to connect to Redis Cluster at {self.host}:{self.port} "
                    f"(Attempt {attempt + 1}/{self.max_retries})"
                )
                
                # Create SSL context for AWS ElastiCache using certifi CA bundle
                ssl_context = create_default_context(cafile=certifi.where())
                ssl_context.check_hostname = True
                ssl_context.verify_mode = CERT_REQUIRED
                
                # Connect to Redis Cluster with TLS support (synchronous client)
                self._client = RedisCluster(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    decode_responses=True,
                    socket_timeout=10,
                    socket_connect_timeout=10,
                    skip_full_coverage_check=True,
                    ssl=True,
                    ssl_context=ssl_context,
                )
                
                # Test connection
                self._client.ping()
                logger.info(f"✓ Redis Cluster connected successfully: {self.host}:{self.port}")
                self._initialized = True
                return
                
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to connect to Redis Cluster after {self.max_retries} attempts")
                    raise
    
    def _run_in_executor(self, func, *args):
        """Run synchronous Redis operation in thread pool."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, func, *args)

    async def get(self, key: str) -> Optional[Any]:
        try:
            await self._ensure_connected()
            # Run synchronous operation in executor to not block event loop
            val = await asyncio.get_event_loop().run_in_executor(
                None, self._client.get, key
            )
            if val is None:
                return None
            try:
                return val.decode() if isinstance(val, bytes) else val
            except AttributeError:
                return val
        except Exception as e:
            logger.error(f"Failed to get key {key} from Redis: {e}")
            raise

    async def set(self, key: str, value: Any) -> None:
        try:
            await self._ensure_connected()
            # convert non-bytes to string
            if not isinstance(value, (bytes, bytearray)):
                value = str(value)
            # Run synchronous operation in executor
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.set, key, value
            )
        except Exception as e:
            logger.error(f"Failed to set key {key} in Redis: {e}")
            raise

    async def append_to_list(self, key: str, value: Any) -> None:
        try:
            await self._ensure_connected()
            if not isinstance(value, (bytes, bytearray)):
                value = str(value)
            # Run synchronous operation in executor
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.rpush, key, value
            )
        except Exception as e:
            logger.error(f"Failed to append to list {key} in Redis: {e}")
            raise

    async def get_list(self, key: str) -> List[Any]:
        try:
            await self._ensure_connected()
            # Run synchronous operation in executor
            entries = await asyncio.get_event_loop().run_in_executor(
                None, self._client.lrange, key, 0, -1
            )
            # decode bytes
            result: List[Any] = []
            for v in entries:
                try:
                    result.append(v.decode() if isinstance(v, bytes) else v)
                except AttributeError:
                    result.append(v)
            return result
        except Exception as e:
            logger.error(f"Failed to get list {key} from Redis: {e}")
            raise

