import sys
from pathlib import Path
from typing import Optional

# Add the parent directory to sys.path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.crewai_agent import CrewAIAgent
from app.router.client import ModelRouterClient
from app.memory.redis import RedisMemory


def create_agent(
    model_router_url: str,
    redis_host: str,
    redis_port: int = 6379,
    redis_password: Optional[str] = None,
) -> CrewAIAgent:
    """Construct a ``CrewAIAgent`` with a preconfigured router and memory.

    Args:
        model_router_url: base URL of the model-router service.
        redis_host: hostname of Redis instance.
        redis_port: port of Redis (default 6379).
        redis_password: optional password for Redis.

    Returns:
        An initialized ``CrewAIAgent`` ready to call ``.run()``.
    """
    router = ModelRouterClient(model_router_url)
    memory = RedisMemory(redis_host, redis_port, redis_password)
    return CrewAIAgent(router=router, memory=memory)
