from typing import Optional

import typer
import asyncio
from dotenv import load_dotenv

load_dotenv()

# ``serve`` conditionally uses uvicorn.  Importing it at the top level
# makes it easier to monkeypatch in unit tests and avoids repeated
# imports when the CLI is invoked multiple times.
try:
    import uvicorn
except ImportError:  # pragma: no cover - tests may patch this
    uvicorn = None  # type: ignore

from .agent import create_agent
from .config import MODEL_ROUTER_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from pathlib import Path
import json

LOG_PATH = Path.home() / ".crew_sessions.json"

app = typer.Typer(help="CLI utilities for CrewAI integration")


@app.command()
def run(
    model_router_url: str = MODEL_ROUTER_URL,
    redis_host: str = REDIS_HOST,
    redis_port: int = REDIS_PORT,
    redis_password: Optional[str] = REDIS_PASSWORD,
):
    """Create and inspect a CrewAIAgent instance."""
    agent = create_agent(model_router_url, redis_host, redis_port, redis_password)
    typer.echo("CrewAIAgent initialized. entering interactive mode; blank session id exits.")

    # wrap for basic logging
    orig_run = agent.run

    async def logged_run(session_id: str, input_text: str, model: str = "gpt-5-nano"):
        resp = await orig_run(session_id=session_id, input_text=input_text, model=model)
        # persist to log file
        entry = {"input": input_text, "response": resp, "model": model}
        logs = {}
        if LOG_PATH.exists():
            try:
                logs = json.loads(LOG_PATH.read_text())
            except Exception:  # fallback if corrupt
                logs = {}
        logs.setdefault(session_id, []).append(entry)
        LOG_PATH.write_text(json.dumps(logs))
        return resp

    agent.run = logged_run  # type: ignore

    # simple REPL so that the run command actually exercises the agent and
    # therefore generates logs
    while True:
        session = typer.prompt("session id (blank to quit)", default="")
        if not session:
            break
        text = typer.prompt("input")
        resp = asyncio.run(agent.run(session, text))
        typer.echo(f"response: {resp}")


@app.command()
def load_persona(path: Path):
    """Load a persona definition from JSON/YAML and print a summary.  In
    a real application this could seed the agent's system prompt or
    memory."""
    if not path.exists():
        typer.echo(f"persona file {path} does not exist")
        raise typer.Exit(code=1)
    content = path.read_text()
    try:
        persona = json.loads(content)
    except Exception:
        try:
            import yaml  # type: ignore

            persona = yaml.safe_load(content)
        except Exception:
            typer.echo("failed to parse persona file")
            raise typer.Exit(code=1)
    typer.echo(f"loaded persona: {persona}")


@app.command()
def replay(session_id: str):
    """Print the conversation transcript for a previously logged session."""
    if not LOG_PATH.exists():
        typer.echo("no sessions logged yet")
        raise typer.Exit(code=1)
    logs = json.loads(LOG_PATH.read_text())
    conv = logs.get(session_id)
    if not conv:
        typer.echo("no conversation found for {session_id}")
        raise typer.Exit(code=1)
    for turn in conv:
        typer.echo(f"USER: {turn['input']}")
        typer.echo(f"AGENT: {turn['response']}\n")



@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 9100,
    reload: bool = False,
):
    """Start the CrewAI FastAPI server using uvicorn.

    Configuration for the model-router and Redis is pulled from the
    ``crew.config`` module which itself reads environment variables.  The
    user simply runs this command and then POSTs to ``/run`` or connects
    to ``/stream``; all heavy lifting happens in the backend.
    """
    if uvicorn is None:
        typer.echo("uvicorn is required to run the server (install crew/requirements.txt)")
        raise typer.Exit(code=1)

    typer.echo(f"starting server on {host}:{port}, reload={reload}")
    uvicorn.run("crew.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
