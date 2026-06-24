from fastapi import FastAPI
from pydantic import BaseModel

from app.config import settings
from app.pipeline.orchestrator import orchestrator

app = FastAPI(title="AI App Compiler")


@app.on_event("startup")
def startup():
    settings.validate()


@app.get("/health")
def health():
    return {"status": "ok", "model": settings.MODEL_NAME}


class PromptRequest(BaseModel):
    prompt: str


@app.post("/pipeline/extract-intent")
def extract_intent(request: PromptRequest):
    state = orchestrator.start(request.prompt)
    return state.model_dump()


@app.post("/pipeline/design-architecture")
def design_architecture(request: PromptRequest):
    """Runs the full pipeline through Stage 2 (intent + architecture)."""
    state = orchestrator.start(request.prompt)
    return state.model_dump()