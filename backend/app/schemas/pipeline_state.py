from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

from app.schemas.intent import IntentSchema
from app.schemas.architecture import ArchitectureSchema
from app.schemas.ui_schema import UISchema
from app.schemas.api_schema import APISchema
from app.schemas.db_schema import DBSchema
from app.schemas.auth_schema import AuthSchema
from app.schemas.business_logic import BusinessLogicSchema


class ValidationIssue(BaseModel):
    layer: Literal["intent", "architecture", "ui", "api", "db", "auth", "business_logic", "cross_layer"]
    severity: Literal["error", "warning"]
    message: str
    field_path: Optional[str] = None


class RepairLogEntry(BaseModel):
    timestamp: str
    layer: str
    issue: str
    action: Literal["repaired", "regenerated", "failed"]
    attempt: int


class PipelineState(BaseModel):
    """Carries state across all pipeline stages. Single source of truth."""

    request_id: str
    raw_prompt: str

    intent: Optional[IntentSchema] = None
    architecture: Optional[ArchitectureSchema] = None
    ui: Optional[UISchema] = None
    api: Optional[APISchema] = None
    db: Optional[DBSchema] = None
    auth: Optional[AuthSchema] = None
    business_logic: Optional[BusinessLogicSchema] = None

    validation_issues: List[ValidationIssue] = Field(default_factory=list)
    repair_log: List[RepairLogEntry] = Field(default_factory=list)

    # Set by CodegenEngine once the Node.js project is written to disk
    generated_app_path: Optional[str] = None

    status: Literal[
        "pending", "intent_done", "architecture_done", "schemas_done",
        "refined", "validated", "repaired", "failed", "needs_clarification",
        "codegen_done", "complete"
    ] = "pending"

    needs_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        extra = "forbid"