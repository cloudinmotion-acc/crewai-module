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
from .orchestration import MultiAgentOrchestrator
from .plugins import Plugin, PluginManager
from .workflows import Workflow
from .memory import MemoryBackend, InMemoryMemory, RedisMemory
from .observability import events



def capabilities() -> dict[str, bool]:
    """Return a summary of the features this module provides.

    This can be used by external tooling to display what the package is
    capable of without needing to inspect the source.  The values are
    simple booleans; more detailed information can be obtained by reading
    the README or introspecting individual objects.
    """
    return {
        "agent_factory": True,
        "standalone_server": True,
        "ws_streaming": True,
        "multi_agent_orchestration": True,
        "plugin_system": True,
        "workflow_framework": True,
        "memory_backends": True,
        "observability": True,
        "cli_tools": True,
    }

__all__ = [
    "create_agent",
    "MultiAgentOrchestrator",
    "Plugin",
    "PluginManager",
    "Workflow",
    "MemoryBackend",
    "InMemoryMemory",
    "RedisMemory",
    "events",
    "capabilities",
]
