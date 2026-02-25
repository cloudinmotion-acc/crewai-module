from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .agent import create_agent
from .config import MODEL_ROUTER_URL, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

app = FastAPI(title="CrewAI Standalone Server")

class CrewRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    input: str = Field(..., description="User input text")
    model: str = Field(default="gpt-5-nano", description="Model to use for generation")

agent = None

@app.on_event("startup")
def on_startup():
    global agent
    agent = create_agent(
        model_router_url=MODEL_ROUTER_URL,
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT,
        redis_password=REDIS_PASSWORD,
    )

@app.post("/run")
async def run_crewai(request: CrewRequest):
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        response = await agent.run(
            session_id=request.session_id,
            input_text=request.input,
            model=request.model,
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
