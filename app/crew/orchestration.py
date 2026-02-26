"""Multi-agent orchestration helpers for CrewAI.

This module provides a very simple manager that keeps a set of
role-named agents and allows one role to send a message to another.  It
is intentionally minimal; you can extend it with broadcast logic,
sub/message queues, or more sophisticated session handling as needed.
"""

from typing import Dict, Optional

from .agent import create_agent
from .observability import events


class AgentRole:
    def __init__(self, name: str, agent: object) -> None:
        self.name = name
        self.agent = agent


class MultiAgentOrchestrator:
    """Manage multiple agents identified by role names."""

    def __init__(
        self,
        model_router_url: str,
        redis_host: str,
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
    ) -> None:
        self.roles: Dict[str, AgentRole] = {}
        self.model_router_url = model_router_url
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_password = redis_password

    def add_role(self, role_name: str) -> None:
        """Create and register a new agent under ``role_name``."""
        agent = create_agent(
            self.model_router_url,
            self.redis_host,
            self.redis_port,
            self.redis_password,
        )
        self.roles[role_name] = AgentRole(role_name, agent)

    async def send_message(
        self,
        from_role: str,
        to_role: str,
        message: str,
        model: str = "gpt-5-nano",
    ) -> str:
        """Send a message from one role to another and return the response.

        This simplistic implementation uses a session id derived from the
        role names so that state is kept per pair.  Real applications may
        wish to manage sessions more deliberately.
        """
        if to_role not in self.roles:
            raise ValueError(f"Unknown role {to_role}")

        session_id = f"{from_role}_to_{to_role}"
        response = await self.roles[to_role].agent.run(
            session_id=session_id,
            input_text=message,
            model=model,
        )
        # emit an observability event for each turn so listeners can
        # log/monitor the conversation.
        events.emit("message", {
            "from": from_role,
            "to": to_role,
            "session_id": session_id,
            "input": message,
            "response": response,
            "model": model,
        })
        return response
