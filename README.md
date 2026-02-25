# CrewAI Module

This directory contains the **CrewAI integration package**, which is
intended to be used alongside the `agent-runtime` and `model-router`
modules.  It provides a lightweight API and optional HTTP service for
running conversation agents using the CrewAI framework.

## Package contents

- `agent.py` – factory that constructs a `CrewAIAgent` object wired with
  a `ModelRouterClient` and `RedisMemory` from the runtime.
- `config.py` – configuration values (from environment variables).
- `runner.py` – small CLI based on [typer](https://typer.tiangolo.com/)
  useful during development.
- `server.py` – minimal FastAPI application exposing `/run` and `/health`
  endpoints; can be run as a standalone service or inside the main
  `agent-runtime` process.
- `tests/` – unit tests verifying basic behaviour of the factory and
  server.

## Getting started

1. Install dependencies from the root repo or the `crew/requirements.txt`.

   ```bash
   pip install -r requirements.txt  # for the full workspace
   # or
   pip install -r crew/requirements.txt
   ```

2. Ensure your `agent-runtime` package is on `PYTHONPATH` or installed
   (the Dockerfile in this directory copies the local `app/` folder for
   this reason).

3. Use the factory in your own code:

   ```python
   from crew.agent import create_agent
   agent = create_agent(
       model_router_url="http://model-router:8000",
       redis_host="localhost",
   )
   response = await agent.run("session1", "Hello")
   ```

4. Run the standalone server (optional):

   ```bash
   uvicorn crew.server:app --reload --port 9100
   ```

## Docker image

A `Dockerfile` is provided for building a container that contains just
this package and its dependencies.  Refer to the top‑level README for
instructions on building and running the image.

## Extending the module

You are encouraged to add CrewAI‑specific features by creating new
modules within this folder and exposing them through the public API.
Several extension scaffolds are already included:

* **Multi-agent orchestration** (`orchestration.py`): maintain named
  roles and route messages between them.  This provides a foundation for
  role‑based conversations, debates, or multi‑agent workflows.
* **Plugin system** (`plugins.py`): register `Plugin` instances that can
  be executed with arbitrary context.  Plugins are ideal for calling
  external APIs, performing actions, or mutating conversation state.

Both subsystems include basic tests in `crew/tests`, which can serve as
templates for your own additions.

Other common extension ideas:

* Workflow/task framework – build higher‑level constructs like “create a
  ticket” or “schedule a meeting” using the conversation history.
* Streaming/WebSocket APIs – return partial responses in real time from
  the server.
* Additional persistence back‑ends – swap Redis for Dynamo/SQL, or add
  long‑term memory helpers.
* Observability hooks – emit events or structured logs for each turn for
  debugging/analytics.
* CLI/SDK improvements – utilities for loading personas, replaying
  sessions, etc.

*Note:* imports within the package currently assume the `agent-runtime`
code is reachable via `sys.path`; once `agent-runtime` is published as a
package this hack can be removed and normal imports used instead.
