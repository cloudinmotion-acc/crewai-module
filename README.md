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

The repository has a simple layout:

```
/ (repo root)
├── Dockerfile            # container build recipe
├── README.md             # this documentation
├── requirements.txt      # Python deps for building/runtime
└── app/
    └── crew/             # actual Python package used at runtime
        ├── __init__.py
        ├── agent.py
        ├── server.py
        └── ...
``` 

When you run the container or install the package, `/app` is added to
`PYTHONPATH` so `import crew` works as before.

This module is designed so that a downstream user need only tell us where
the model-router and Redis are located via environment variables or the
`config.py` defaults.  All of the heavy logic – agent management,
workflows, plugins, observability – lives behind the API; the user simply
selects this package, runs the server, and POSTs requests or connects via
WebSocket.  No additional configuration is required for the basic use
case.

1. Install dependencies from the root repo or the `requirements.txt` in the repository:

   ```bash
   pip install -r requirements.txt  # for the full workspace
   ```

2. Provide configuration by setting environment variables (or edit
   `crew/config.py`):

   ```bash
   export MODEL_ROUTER_URL="http://model-router:8000"
   export REDIS_HOST="redis.local"
   export REDIS_PORT=6379
   export REDIS_PASSWORD="..."
   ```

3. Run the server – either directly with uvicorn or via the CLI helper:

   ```bash
   # using the CLI since it comes built-in:
   python -m crew.runner serve --host 0.0.0.0 --port 9100

   # or equivalently:
   uvicorn crew.server:app --reload --port 9100
   ```

   The process will print its listening address.  At this point the user
   is ready to call the API; the backend handles all orchestration, memory,
   and model calls.

4. Example request:

   ```bash
   curl -X POST http://localhost:9100/run \
     -H 'Content-Type: application/json' \
     -d '{"session_id":"s1","input":"Hello"}'
   ```

   Resulting JSON will contain the agent's response.  Subsequent turns may
   reuse the same `session_id` for context.

For now, the server is the primary component the user interacts with; the
other utilities (multi‑agent orchestrator, workflows, plugins, etc.) are
available for later extension (v2).  The package also exposes a small
helper:

```python
import crew
print(crew.capabilities())
```

which returns a dictionary of features.  This is useful if the end user
is selecting the module from a catalogue and needs to know what it can
do without reading the source.

The rest of this README documents the underlying features in detail if you
or another developer want to build on top of the basic server.

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

* **Workflow/task framework** – chain asynchronous steps into a workflow
  object.  See ``crew/workflows.py`` for the base classes and a simple
  ticket-creation example.
* **Streaming/WebSocket APIs** – the FastAPI server now exposes a
  ``/stream`` websocket endpoint that yields partial chunks as they're
  produced.  This can be backed by the model-router's streaming API or a
  custom generator.
* **Additional persistence back‑ends** – the new ``crew/memory.py``
  defines a ``MemoryBackend`` interface and ships with an
  ``InMemoryMemory`` implementation.  ``agent.create_agent`` accepts any
  backend, so you can drop in Dynamo, SQL, or a long-term store.
* **Observability hooks** – ``crew/observability.py`` provides a simple
  ``EventEmitter``; both the orchestrator and server emit events on each
  turn.  Listeners can log, export metrics, or drive analytics.
* **CLI/SDK improvements** – ``crew/runner.py`` now includes commands to
  load personas and replay sessions.  The ``run`` command also logs
  interactions to ``~/.crew_sessions.json`` automatically.

In the sections below we provide a complete usage guide covering these
features.

---

## Detailed guide

### Multi-agent orchestration

The ``MultiAgentOrchestrator`` class lets you register agents under
role names and pass messages between them.  Each message pair shares a
session identifier so history is preserved per conversation.

```python
from crew.orchestration import MultiAgentOrchestrator

orch = MultiAgentOrchestrator(
    model_router_url="http://router:8000",
    redis_host="localhost",
)
orch.add_role("alice")
orch.add_role("bob")

resp = await orch.send_message("alice", "bob", "hello")
```

Events are emitted for every turn; you can add listeners with
``crew.observability.events.on("message", callback)``.

### Plugin system

Register custom ``Plugin`` instances to run before or after agent
invocations.  The server exposes hooks on the ``/run`` endpoint.

```python
from crew.plugins import Plugin, PluginManager

class LogPlugin(Plugin):
    async def run(self, ctx):
        print("running with", ctx)

pm = PluginManager()
pm.register("pre_run", LogPlugin())
```

Plugins receive a mutable context dictionary and may alter it or call
external services.

### Workflows/tasks

Create high‑level workflows by assembling async steps that operate on a
shared context.

```python
from crew.workflows import Workflow

async def collect_info(ctx):
    ctx["description"] = "user supplied text"

async def call_api(ctx):
    ctx["ticket_id"] = "TICKET-1234"

wf = Workflow("create_ticket").add_step(collect_info).add_step(call_api)
result = await wf.run({})
```

Workflows make it easy to encapsulate business logic on top of
conversational state.

### Streaming API

The standalone server now supports a WebSocket endpoint:

```bash
wscat -c ws://localhost:9100/stream
# send {"session_id":"s1","input":"hello"}
```

It will emit an object containing ``chunk`` for each piece of the
response, then a final ``{"done": true}`` message.  You can wire this
up to a browser or other real‑time client.

### Memory backends

By default ``create_agent`` uses Redis, but any ``MemoryBackend`` can be
supplied.  The provided ``InMemoryMemory`` is useful for tests or CLI
interactions:

```python
from crew.agent import create_agent
from crew.memory import InMemoryMemory

agent = create_agent(
    model_router_url="http://router:8000",
    memory=InMemoryMemory(),
)
```

You can implement custom backends by subclassing ``MemoryBackend``.

### Observability

The global ``crew.observability.events`` emitter is used by both the
orchestrator and server.  Subscribe to ``"message"`` or ``"turn"``
events to capture data:

```python
from crew.observability import events

def listener(data):
    print("event", data)

events.on("turn", listener)
```

### CLI & SDK

The ``crew/runner.py`` script offers several handy utilities:

* ``crew-run run`` – instantiate an agent and print usage hints.  All
  interactions made through this command are logged automatically to
  ``~/.crew_sessions.json``.
* ``crew-run load-persona <path>`` – load and display a persona JSON or
  YAML file.
* ``crew-run replay <session_id>`` – print the entire conversation for a
  given session from the log file.

You can import ``crew.runner`` from Python and use the Typer app in
other programs as well.

---

The package remains deliberately lightweight; feel free to extend any of
these components or replace the defaults to suit your needs.

*Note:* imports within the package currently assume the `agent-runtime`
code is reachable via `sys.path`; once `agent-runtime` is published as a
package this hack can be removed and normal imports used instead.
