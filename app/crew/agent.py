import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.crewai_agent import CrewAIAgent
from app.router.client import ModelRouterClient
# we still import RedisMemory for compatibility in the default factory
from app.memory.redis import RedisMemory as _RuntimeRedisMemory

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
    if memory is None:
        if redis_host is None:
            raise ValueError("either memory or redis_host must be provided")
        # prefer the Crew-specific wrapper so we satisfy our interface
        memory = CrewRedisMemory(redis_host, redis_port, redis_password)
    return CrewAIAgent(router=router, memory=memory)
