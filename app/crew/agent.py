from typing import Optional

from ..agents.crewai_agent import CrewAIAgent
from ..router.client import ModelRouterClient
# we still import RedisMemory for compatibility in the default factory
from ..memory.redis import RedisMemory as _RuntimeRedisMemory

from .memory import MemoryBackend, RedisMemory as CrewRedisMemory, InMemoryMemory


def create_agent(
    model_router_url: str,
    redis_host: Optional[str] = None,
    redis_port: int = 6379,
    redis_password: Optional[str] = None,
    memory: Optional[MemoryBackend] = None,
) -> CrewAIAgent:
    """Construct a ``CrewAIAgent`` with a preconfigured router and memory.

    The original signature accepted Redis connection settings and built a
    ``RedisMemory``.  We now allow callers to pass any
    ``MemoryBackend`` (e.g. ``InMemoryMemory`` for tests or CLI replay).
    If both ``memory`` and Redis parameters are provided the explicit
    ``memory`` object takes precedence.
    """
    router = ModelRouterClient(model_router_url)
    if memory is not None:
        chosen = memory
    elif redis_host:
        # use real Redis if host provided
        chosen = CrewRedisMemory(redis_host, redis_port, redis_password)  # type: ignore
    else:
        # fallback to in‑memory storage for local development/tests
        chosen = InMemoryMemory()
    return CrewAIAgent(router=router, memory=chosen)
