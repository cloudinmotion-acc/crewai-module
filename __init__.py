"""Top-level package for the CrewAI integration module.

This package is intended to sit alongside the existing
`agent-runtime` and `model-router` modules.  It provides a small,
opinionated API that lets users "plug" a CrewAI framework into the
runtime, wiring up a model router and Redis memory with minimal
configuration.

Example usage:

```python
import crew
agent = crew.create_agent(
    model_router_url="http://localhost:8000",
    redis_host="localhost",
)
response = await agent.run("session1", "Hello", model="gpt-5-nano")
```
"""

from .agent import create_agent  # public API

__all__ = ["create_agent"]
