from typing import Optional

import typer

from .agent import create_agent
from .config import MODEL_ROUTER_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

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
    typer.echo("CrewAIAgent initialized\nUse `agent.run(session_id, input_text, model)` in Python to interact.")


if __name__ == "__main__":
    app()
