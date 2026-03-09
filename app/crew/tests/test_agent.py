import pytest
import json

# the package lives under "app"; tests need the full qualification so
# relative imports inside the module resolve correctly
from app.crew.agent import create_agent


def test_create_agent_minimal():
    # We only verify that creation succeeds; real integration tests would
    # require a running ModelRouter and Redis instance.  To avoid
    # pulling in the full runtime package we supply an in-memory memory
    # backend here.
    from app.crew.memory import InMemoryMemory

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
    from app.crew.agent import create_agent
    from app.crew.memory import InMemoryMemory

    mem = InMemoryMemory()
    agent = create_agent("http://localhost:8000", memory=mem)
    assert agent is not None
    assert hasattr(agent, "run")
    # underlying memory should be the same instance
    assert agent.memory is mem

    # verify the stubbed agent can actually run and echoes input
    import asyncio

    # monkeypatch router to avoid real network call
    async def fake_generate(prompt, model="", state=None):
        return {"response": f"echo:{prompt}", "state": state or {}}
    agent.router.generate = fake_generate  # type: ignore

    resp = asyncio.run(agent.run("sid", "hello", model="test-model"))
    assert resp == "echo:hello"




def test_agent_state_and_router(monkeypatch):
    # ensure agent passes state to router and persists returned state
    from app.crew.agent import create_agent
    from app.crew.memory import InMemoryMemory

    mem = InMemoryMemory()
    agent = create_agent("http://localhost:8000", memory=mem)

    called = {}

    async def fake_generate(prompt, model="", state=None):
        # record incoming prompt/state
        called['prompt'] = prompt
        called['state'] = state
        # return response and increment counter in state
        new_state = {**(state or {}), 'count': state.get('count', 0) + 1 if state else 1}
        return {"response": "resp", "state": new_state}

    agent.router.generate = fake_generate  # type: ignore
    import asyncio
    resp1 = asyncio.run(agent.run("s", "hi", model="m"))
    assert resp1 == "resp"
    # after first call state should count=1
    raw = asyncio.run(mem.get("state:s"))
    assert raw is not None
    stored = json.loads(raw)
    assert stored.get('count') == 1

    # second call should see previous state
    resp2 = asyncio.run(agent.run("s", "hey", model="m"))
    assert resp2 == "resp"
    assert called['state']['count'] == 1


def test_capabilities_exported():
    import crew

    caps = crew.capabilities()
    assert isinstance(caps, dict)
    assert caps.get("standalone_server") is True
    assert caps.get("plugin_system") is True

def test_model_router_client(monkeypatch):
    # ensure client issues POST to /generate and returns field
    from app.router.client import ModelRouterClient
    calls = []

    class DummyResp:
        def __init__(self, data):
            self._data = data
            self.status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return self._data
        @property
        def text(self):
            return "raw"

    class DummyClient:
        def __init__(self, base_url, timeout):
            pass
        async def post(self, path, json):
            calls.append((path, json))
            return DummyResp({"output": "ok"})
        async def aclose(self):
            pass

    monkeypatch.setattr("app.router.client.httpx.AsyncClient", DummyClient)
    router = ModelRouterClient("http://localhost:8000")
    import asyncio
    result = asyncio.run(router.generate("hi", model="m"))
    # expect the raw JSON dict here
    assert isinstance(result, dict)
    assert result.get("output") == "ok"
    assert calls == [("/generate", {"prompt": "hi", "model": "m"})]


def test_redis_memory(monkeypatch):
    # monkeypatch underlying aioredis.Redis class to a fake in-memory object
    from crew import memory

    class FakeRedis:
        def __init__(self, host, port, password):
            self.store = {}
            self.lists = {}
        async def get(self, key):
            return self.store.get(key)
        async def set(self, key, val):
            self.store[key] = val
        async def rpush(self, key, val):
            self.lists.setdefault(key, []).append(val)
        async def lrange(self, key, a, b):
            return self.lists.get(key, [])

    monkeypatch.setattr(memory, "aioredis", type("mod", (), {"Redis": FakeRedis}))

    mem = memory.RedisMemory("h", 1, "p")
    import asyncio

    async def do_test():
        await mem.set("foo", "bar")
        assert await mem.get("foo") == "bar"
        await mem.append_to_list("alist", 1)
        await mem.append_to_list("alist", 2)
        assert await mem.get_list("alist") == [1, 2]

    asyncio.run(do_test())


def test_create_agent_uses_redis(monkeypatch):
    # ensure create_agent picks RedisMemory when redis_host provided
    from app.crew.agent import create_agent
    from crew import memory

    class DummyRedis(memory.RedisMemory):
        def __init__(self, host, port, password):
            self.params = (host, port, password)
    monkeypatch.setattr(memory, "RedisMemory", DummyRedis)

    agent = create_agent("url", redis_host="h", redis_port=2, redis_password="p")
    assert isinstance(agent.memory, DummyRedis)
    assert agent.memory.params == ("h", 2, "p")


def test_workflow_simple(monkeypatch):
    from app.crew.workflows import Workflow
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
    from app.crew.observability import events

    called = {}

    def listener(data):
        called.update(data)

    events.on("test_event", listener)
    events.emit("test_event", {"x": 1})
    assert called.get("x") == 1



def test_plugin_manager():
    from app.crew.plugins import PluginManager, Plugin

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
    from app.crew.orchestration import MultiAgentOrchestrator

    class FakeAgent:
        async def run(self, session_id, input_text, model):
            return f"echo:{input_text}"

    # patch create_agent to return FakeAgent
    monkeypatch.setattr("crew.orchestration.create_agent", lambda *args, **kwargs: FakeAgent())

    orchestrator = MultiAgentOrchestrator("url", "rhost")
    orchestrator.add_role("alice")
    orchestrator.add_role("bob")

    # listen for the message event
    from app.crew.observability import events
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
