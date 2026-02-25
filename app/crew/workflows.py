"""Workflow and task framework for CrewAI.

This light framework allows you to chain together multiple asynchronous
steps to accomplish a higher-level task (e.g. create a ticket,
schedule a meeting).  Each step receives a mutable "context" dictionary
that can be shared across steps.  Workflows themselves are just named
collections of steps with a small runner API.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List

Step = Callable[[Dict[str, Any]], Awaitable[None]]


class Workflow:
    def __init__(self, name: str) -> None:
        self.name = name
        self.steps: List[Step] = []

    def add_step(self, step: Step) -> "Workflow":
        """Append a new step to the workflow."""
        self.steps.append(step)
        return self

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all steps in sequence, passing the same context dict."""
        for step in self.steps:
            await step(context)
        return context


# convenience helpers for common patterns
async def echo_step(context: Dict[str, Any]) -> None:  # pragma: no cover - example
    """A trivial step that copies ``input`` -> ``echo``."""
    context["echo"] = context.get("input", "")


# example pre-defined workflows (users can build their own too)

def ticket_creation_workflow() -> Workflow:  # pragma: no cover - example
    w = Workflow("create_ticket")

    async def check_input(ctx: Dict[str, Any]) -> None:
        if "description" not in ctx:
            raise ValueError("description required to create ticket")

    async def call_ticket_api(ctx: Dict[str, Any]) -> None:
        # pretend to call external service
        ctx["ticket_id"] = "TICKET-1234"

    w.add_step(check_input).add_step(call_ticket_api)
    return w

