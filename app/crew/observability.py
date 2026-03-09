"""Observability helpers for CrewAI.

Provides a lightweight event emitter that components can use to
publish and subscribe to events (e.g. conversation turns, errors,
external API calls).  This allows external tools or monitoring systems to
hook into the runtime without tightly coupling to the core code.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List


class EventEmitter:
    def __init__(self) -> None:
        # map event name to list of callbacks
        self._listeners: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def on(self, event: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a listener for an event."""
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event: str, data: Dict[str, Any]) -> None:
        """Emit an event to all registered listeners. Any exceptions from
        listeners are caught and logged internally so they don't disrupt the
        main flow."""
        for cb in self._listeners.get(event, []):
            try:
                cb(data)
            except Exception:
                # swallow exceptions; observers shouldn't crash the app
                pass


# single shared emitter that packages can import
events = EventEmitter()
