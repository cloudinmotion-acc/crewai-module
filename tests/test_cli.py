from typer.testing import CliRunner
from crew import runner
import json
import tempfile
from pathlib import Path

runner.LOG_PATH = Path(tempfile.mktemp())  # redirect log path for tests


def test_load_persona(tmp_path, monkeypatch):
    file = tmp_path / "persona.json"
    file.write_text(json.dumps({"name": "bot", "prompt": "hi"}))
    result = CliRunner().invoke(runner.app, ["load-persona", str(file)])
    assert result.exit_code == 0
    assert "loaded persona" in result.stdout


def test_replay_no_sessions(monkeypatch):
    # ensure replay gracefully handles missing file
    if runner.LOG_PATH.exists():
        runner.LOG_PATH.unlink()
    result = CliRunner().invoke(runner.app, ["replay", "sess1"])
    assert result.exit_code != 0


def test_run_logs(monkeypatch):
    # fake agent so we can run without network
    class FakeAgent:
        async def run(self, session_id, input_text, model):
            return f"echo:{input_text}"

    monkeypatch.setattr("crew.runner.create_agent", lambda *args, **kwargs: FakeAgent())
    # run the CLI and provide defaults
    # simulate entering a session id, a message, then quitting
    input_data = "s1\nhello\n\n"
    result = CliRunner().invoke(runner.app, ["run"], input=input_data)
    assert result.exit_code == 0
    # after running, log file should contain the session entry
    logs = json.loads(runner.LOG_PATH.read_text())
    assert "s1" in logs
    assert logs["s1"][0]["input"] == "hello"
    assert logs["s1"][0]["response"] == "echo:hello"


def test_serve_command(monkeypatch):
    # ensure serve invokes uvicorn.run with correct args
    class Dummy:
        def run(self, app, host, port, reload):
            # record parameters for assertion
            Dummy.called = (app, host, port, reload)

    monkeypatch.setattr("crew.runner.uvicorn", Dummy())
    result = CliRunner().invoke(runner.app, ["serve", "--host", "127.0.0.1", "--port", "8000"])
    assert result.exit_code == 0
    assert Dummy.called[0] == "crew.server:app"
    assert Dummy.called[1] == "127.0.0.1"
    assert Dummy.called[2] == 8000
