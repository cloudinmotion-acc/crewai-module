from fastapi.testclient import TestClient
from crew.server import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_run_and_plugins(monkeypatch):
    # patch agent factory so the startup handler assigns our fake
    class FakeAgent:
        async def run(self, session_id, input_text, model):
            return f"echo:{input_text}"

    monkeypatch.setattr("crew.server.create_agent", lambda *a, **k: FakeAgent())

    # use context manager to ensure startup/shutdown events execute
    with TestClient(app) as client:
        # register a simple plugin that tags the context
        from crew.plugins import Plugin

        class TagPlugin(Plugin):
            async def run(self, context):
                context["tagged"] = True

        from crew.server import plugin_manager
        # clear existing plugins to avoid state from other tests
        plugin_manager._plugins.clear()
        plugin_manager.register("pre_run", TagPlugin())

        resp = client.post("/run", json={"session_id": "s1", "input": "hello"})
        assert resp.status_code == 200
        assert resp.json()["response"] == "echo:hello"
        # plugin should have executed without error--no direct output but no crash


def test_streaming(monkeypatch):
    class FakeAgent:
        async def run(self, session_id, input_text, model):
            return "one two three"

    monkeypatch.setattr("crew.server.agent", FakeAgent())
    client = TestClient(app)
    with client.websocket_connect("/stream") as ws:
        ws.send_json({"session_id": "s", "input": "hi"})
        chunks = []
        while True:
            msg = ws.receive_json()
            if "chunk" in msg:
                chunks.append(msg["chunk"])
            elif msg.get("done"):
                break
        assert chunks == ["one", "two", "three"]
