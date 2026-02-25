import os
from typing import Optional

MODEL_ROUTER_URL: str = os.getenv("MODEL_ROUTER_URL", "http://localhost:8000")
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
