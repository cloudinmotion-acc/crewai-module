"""Plugin system for CrewAI.

Users can register custom ``Plugin`` implementations that the
conversational agent invokes during processing.  This enables action
handlers, API calls, tool integrations, etc.

Example:

```python
class MyToolPlugin(Plugin):
    async def run(self, context):
        # inspect context and modify it
        context["tool_output"] = "result"

pm = PluginManager()
pm.register("tool", MyToolPlugin())
await pm.execute("tool", {"input":"hi"})
```

Plugins are intentionally lightweight; they receive a mutable context
dictionary and may update it in place.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Plugin(ABC):
    """Abstract base class for CrewAI plugins."""

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> None:  # pragma: no cover - interface
        """Perform the plugin action.

        ``context`` is a mutable dictionary containing arbitrary
        information about the conversation.  Plugins may read or write
        keys as needed.
        """
        pass


class PluginManager:
    """Registry and executor for plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}

    def register(self, name: str, plugin: Plugin) -> None:
        """Register a plugin under the given name."""
        if name in self._plugins:
            raise ValueError(f"plugin '{name}' already registered")
        self._plugins[name] = plugin

    def get(self, name: str) -> Plugin:
        return self._plugins[name]

    def list(self) -> list[str]:
        return list(self._plugins.keys())

    async def execute(self, name: str, context: Dict[str, Any]) -> None:
        plugin = self.get(name)
        await plugin.run(context)
