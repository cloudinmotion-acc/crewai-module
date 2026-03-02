from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging
import traceback
from dotenv import load_dotenv

load_dotenv()

from .agent import create_agent
from .config import MODEL_ROUTER_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from .observability import events
from .plugins import PluginManager
from fastapi import WebSocket

logger = logging.getLogger(__name__)

app = FastAPI(title="CrewAI Standalone Server")

class CrewRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    input: str = Field(..., description="User input text")
    model: str = Field(default="gpt-5-nano", description="Model to use for generation")

agent = None
plugin_manager = PluginManager()

@app.on_event("startup")
def on_startup():
    global agent
    logger.info(f"creating agent using router={MODEL_ROUTER_URL}, redis={REDIS_HOST}:{REDIS_PORT}")
    agent = create_agent(
        model_router_url=MODEL_ROUTER_URL,
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT,
        redis_password=REDIS_PASSWORD,
    )
    logger.info(f"agent created with memory={type(agent.memory).__name__}")

@app.post("/run")
async def run_crewai(request: CrewRequest):
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        # allow plugins to mutate request context before running
        context = {
            "session_id": request.session_id,
            "input": request.input,
            "model": request.model,
        }
        await plugin_manager.execute("pre_run", context)
        response = await agent.run(
            session_id=request.session_id,
            input_text=request.input,
            model=request.model,
        )
        events.emit("turn", {
            "session_id": request.session_id,
            "input": request.input,
            "response": response,
            "model": request.model,
        })
        # post-run plugins
        context["response"] = response
        await plugin_manager.execute("post_run", context)
        return {"response": response}
    except Exception as e:
        error_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Error in /run endpoint: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/plugins/{name}")
def register_plugin(name: str):
    """Register a plugin by name. This is a very lightweight API that
    inner processes or external orchestrators can call to add behaviour
    at runtime.  In a production system you'd likely provide a more
    robust mechanism (e.g. loading from Python modules)."""
    # for simplicity we just expect the caller to have imported the
    # Plugin subclass and placed it on the app state.
    raise HTTPException(status_code=501, detail="dynamic plugin registration not implemented")


@app.websocket("/stream")
async def stream_crewai(websocket: WebSocket):
    """WebSocket endpoint that sends partial responses as they are
    generated.  Here we simulate streaming by breaking the full response
    into whitespace-separated chunks.  A real implementation would rely
    on the model-router's streaming API.
    """
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        session_id = data.get("session_id")
        input_text = data.get("input")
        model = data.get("model", "gpt-5-nano")
        if agent is None:
            await websocket.send_json({"error": "agent not initialized"})
            await websocket.close()
            return
        # run the synchronous call and chunk the result; replace with
        # proper async streaming when supported by the router/client.
        full = await agent.run(session_id=session_id, input_text=input_text, model=model)
        for piece in full.split():
            await websocket.send_json({"chunk": piece})
        await websocket.send_json({"done": True})
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
