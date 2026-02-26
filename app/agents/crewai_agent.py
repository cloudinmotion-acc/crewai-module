"""Lightweight stand-in for the full runtime's CrewAIAgent.

The real agent implementation lives in the `agent-runtime` project and
is not part of this repository.  We provide a minimal class here so that
`create_agent` can import successfully and the package works in isolation
(e.g. during local development or when building the Docker image).

The stub simply echoes input text; callers should replace or extend it
with the real implementation when running within the full runtime.
"""

from __future__ import annotations
from typing import Any


class CrewAIAgent:
    def __init__(self, router: Any, memory: Any) -> None:
        self.router = router
        self.memory = memory

    async def run(self, session_id: str, input_text: str, model: str = "gpt-5-nano") -> str:
        """Perform a conversation turn.

        This stub implementation ignores the router and simply returns an
        echo of the input text.  The real class would call the
        ``ModelRouterClient`` and manage conversation state.
        """
        # record a simple memory entry if the backend supports it
        try:
            await self.memory.set(
                f"last_input:{session_id}", input_text  # type: ignore
            )
        except Exception:  # pragma: no cover - memory may be sync
            pass
        return f"echo:{input_text}"
