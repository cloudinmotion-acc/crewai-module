import pytest

from crew.agent import create_agent


def test_create_agent_minimal():
    # We only verify that creation succeeds; real integration tests would
    # require a running ModelRouter and Redis instance.  To avoid
    # pulling in the full runtime package we supply an in-memory memory
    # backend here.
    from crew.memory import InMemoryMemory

    agent = create_agent("http://localhost:8000", memory=InMemoryMemory())
    assert agent is not None
    assert hasattr(agent, "run")


def test_memory_inmemory():
    from crew.memory import InMemoryMemory

    mem = InMemoryMemory()
    import asyncio

    async def do_test():
        await mem.set("foo", "bar")
        assert await mem.get("foo") == "bar"
        await mem.append_to_list("alist", 1)
        await mem.append_to_list("alist", 2)
        assert await mem.get_list("alist") == [1, 2]

    asyncio.run(do_test())


def test_create_agent_with_custom_memory():
    from crew.agent import create_agent
    from crew.memory import InMemoryMemory

    mem = InMemoryMemory()
    agent = create_agent("http://localhost:8000", memory=mem)
    assert agent is not None
    assert hasattr(agent, "run")
    # underlying memory should be the same instance
    assert agent.memory is mem


def test_capabilities_exported():
    import crew

    caps = crew.capabilities()
    assert isinstance(caps, dict)
    assert caps.get("standalone_server") is True
    assert caps.get("plugin_system") is True


def test_workflow_simple(monkeypatch):
    from crew.workflows import Workflow
    import asyncio

    async def step1(ctx):
        ctx["a"] = 1

    async def step2(ctx):
        ctx["b"] = ctx.get("a", 0) + 1

    wf = Workflow("test").add_step(step1).add_step(step2)
    ctx = {}
    asyncio.run(wf.run(ctx))
    assert ctx == {"a": 1, "b": 2}


def test_observability_hooks(monkeypatch):
    from crew.observability import events

    called = {}

    def listener(data):
        called.update(data)

    events.on("test_event", listener)
    events.emit("test_event", {"x": 1})
    assert called.get("x") == 1



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

    # listen for the message event
    from crew.observability import events
    seen = {}

    def on_msg(data):
        seen.update(data)

    events.on("message", on_msg)

    import asyncio
    resp = asyncio.run(orchestrator.send_message("alice", "bob", "hi"))
    assert resp == "echo:hi"
    assert seen.get("from") == "alice"
    assert seen.get("to") == "bob"
    assert seen.get("response") == "echo:hi"
