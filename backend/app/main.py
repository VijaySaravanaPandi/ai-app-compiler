"""
FastAPI application — AI App Compiler
======================================
Endpoints:
  POST /compile           — run full pipeline synchronously
  POST /compile/async     — fire-and-forget, returns request_id
  GET  /compile/status/{request_id}  — poll pipeline status
  GET  /apps/{request_id}/download   — download generated app as .zip
  GET  /health            — basic health check
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import settings
from app.pipeline.orchestrator import orchestrator
from app.schemas.pipeline_state import PipelineState

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI App Compiler",
    description="Natural language → validated config → runnable Node.js app",
    version="1.0.0",
)


@app.on_event("startup")
def startup() -> None:
    settings.validate()


# ── In-memory status store (replace with Redis/DB in production) ───────────────
_pipeline_status: Dict[str, PipelineState] = {}


# ── Request / response models ─────────────────────────────────────────────────
class CompileRequest(BaseModel):
    prompt: str

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics."
            }
        }


class AsyncCompileResponse(BaseModel):
    request_id: str
    status: str
    message: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _run_pipeline(request_id: str, prompt: str) -> None:
    """Run the full pipeline and cache the result."""
    try:
        state = orchestrator.start(prompt)
        # Override the auto-generated request_id so status polling works
        state.request_id = request_id
    except Exception as exc:  # defensive — should never propagate here
        state = PipelineState(request_id=request_id, raw_prompt=prompt)
        state.status = "failed"
        from app.schemas.pipeline_state import ValidationIssue
        state.validation_issues.append(
            ValidationIssue(layer="cross_layer", severity="error", message=str(exc))
        )
    _pipeline_status[request_id] = state


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    """Basic health-check endpoint."""
    return {"status": "ok", "model": settings.MODEL_NAME}


@app.post("/compile", response_model=None, tags=["Pipeline"])
def compile_sync(request: CompileRequest):
    """
    Run the full pipeline synchronously and return the complete PipelineState.

    For large/complex prompts this may take 30-120 s depending on model latency.
    Use **/compile/async** + **/compile/status** for non-blocking calls.
    """
    request_id = str(uuid.uuid4())
    _run_pipeline(request_id, request.prompt)
    state = _pipeline_status[request_id]
    return state.model_dump()


@app.post("/compile/async", response_model=AsyncCompileResponse, tags=["Pipeline"])
async def compile_async(request: CompileRequest, background_tasks: BackgroundTasks):
    """
    Fire-and-forget version.  Returns a ``request_id`` immediately.
    Poll **/compile/status/{request_id}** to check progress.
    """
    request_id = str(uuid.uuid4())
    # Initialise status as pending so the poller can see it immediately
    _pipeline_status[request_id] = PipelineState(
        request_id=request_id, raw_prompt=request.prompt, status="pending"
    )
    background_tasks.add_task(_run_pipeline, request_id, request.prompt)
    return AsyncCompileResponse(
        request_id=request_id,
        status="pending",
        message="Pipeline started. Poll /compile/status/{request_id} for updates.",
    )


@app.get("/compile/status/{request_id}", tags=["Pipeline"])
def compile_status(request_id: str):
    """Poll the status of an async pipeline run."""
    state = _pipeline_status.get(request_id)
    if state is None:
        raise HTTPException(status_code=404, detail="request_id not found")
    return state.model_dump()


@app.get("/apps/{request_id}/download", tags=["Codegen"])
def download_app(request_id: str):
    """Download the generated Node.js application as a .zip file."""
    state = _pipeline_status.get(request_id)
    if state is None:
        raise HTTPException(status_code=404, detail="request_id not found")
    if state.generated_app_path is None:
        raise HTTPException(status_code=400, detail="App has not been generated yet")

    project_dir = Path(state.generated_app_path)
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Generated app directory not found")

    from app.codegen.generator import codegen_engine
    zip_path = codegen_engine.zip_project(project_dir)
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"{request_id}.zip",
    )


# ── Frontend static files ─────────────────────────────────────────────────────
_FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")