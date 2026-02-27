"""Lightweight stand-in for the full runtime's CrewAIAgent.

The real agent implementation lives in the `agent-runtime` project and
is not part of this repository.  We provide a minimal class here so that
`create_agent` can import successfully and the package works in isolation
(e.g. during local development or when building the Docker image).

The stub simply echoes input text; callers should replace or extend it
with the real implementation when running within the full runtime.
"""

from __future__ import annotations
import json
from typing import Any, Dict


class CrewAIAgent:
    def __init__(self, router: Any, memory: Any) -> None:
        self.router = router
        self.memory = memory

    async def run(self, session_id: str, input_text: str, model: str = "gpt-5-nano") -> str:
        """Perform a conversation turn using the model router.

        Maintains a simple ``state`` dictionary in memory under
        ``state:{session_id}``, which may include a ``history`` list of
        messages.  The router is expected to accept and return this state.
        """
        try:
            # load old state or start fresh
            raw_state = await self.memory.get(f"state:{session_id}")  # type: ignore
            state: dict = {} if raw_state is None else json.loads(raw_state)  # type: ignore

            history = state.get("history", [])

            # add user message to history
            history.append({"role": "user", "content": input_text})
            state["history"] = history

            # call router with state
            result = await self.router.generate(prompt=input_text, model=model, state=state)  # type: ignore

            # result may be a dict or raw text
            if isinstance(result, dict):
                response_text = result.get("response") or result.get("output") or result.get("text", "")
                # update state if returned
                if "state" in result:
                    state = result["state"]
            else:
                response_text = str(result)

            # append assistant to history and save state
            history.append({"role": "assistant", "content": response_text})
            state["history"] = history
            await self.memory.set(f"state:{session_id}", json.dumps(state))  # type: ignore

            # also keep simple history list for backwards compatibility
            await self.memory.append_to_list(f"history:{session_id}", f"User: {input_text}")  # type: ignore
            await self.memory.append_to_list(f"history:{session_id}", f"Assistant: {response_text}")  # type: ignore

            await self.memory.set(f"last_input:{session_id}", input_text)  # type: ignore
            await self.memory.set(f"last_output:{session_id}", response_text)  # type: ignore

            return response_text
        except Exception as e:  # pragma: no cover - memory may be sync
            # Fallback if memory is unavailable
            try:
                response = await self.router.generate(input_text, model=model)  # type: ignore
                return response if isinstance(response, str) else str(response)
            except Exception:
                raise

