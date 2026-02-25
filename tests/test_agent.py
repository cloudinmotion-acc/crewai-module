import pytest

from crew.agent import create_agent


def test_create_agent_minimal():
    # We only verify that creation succeeds; real integration tests would
    # require a running ModelRouter and Redis instance.
    agent = create_agent("http://localhost:8000", "clustercfg.test1h25feb-redis-dev.gcvryk.use1.cache.amazonaws.com", 6379, "ERM4Nt7bMpxepZMk")
    assert agent is not None
    assert hasattr(agent, "run")


def test_plugin_manager():
    from crew.plugins import PluginManager, Plugin

    class Dummy(Plugin):
        async def run(self, context):
            context["foo"] = "bar"

    pm = PluginManager()
    pm.register("dummy", Dummy())
    ctx = {}
    import asyncio

    asyncio.run(pm.execute("dummy", ctx))
    assert ctx["foo"] == "bar"


def test_orchestrator_roles(monkeypatch):
    from crew.orchestration import MultiAgentOrchestrator

    class FakeAgent:
        async def run(self, session_id, input_text, model):
            return f"echo:{input_text}"

    # patch create_agent to return FakeAgent
    monkeypatch.setattr("crew.orchestration.create_agent", lambda *args, **kwargs: FakeAgent())

    orchestrator = MultiAgentOrchestrator("url", "rhost")
    orchestrator.add_role("alice")
    orchestrator.add_role("bob")

    import asyncio
    resp = asyncio.run(orchestrator.send_message("alice", "bob", "hi"))
    assert resp == "echo:hi"
