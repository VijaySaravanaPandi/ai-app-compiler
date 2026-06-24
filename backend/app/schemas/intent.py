from pydantic import BaseModel, Field
from typing import List


class IntentSchema(BaseModel):
    """Structured output of Stage 1 — Intent Extraction."""

    app_name: str = Field(..., description="Short name for the app, derived or inferred")
    app_type: str = Field(..., description="e.g. crm, ecommerce, blog, dashboard, social")
    core_features: List[str] = Field(default_factory=list, description="Explicit features requested")
    entities_mentioned: List[str] = Field(default_factory=list, description="Nouns implying data entities, e.g. 'contacts', 'orders'")
    roles_mentioned: List[str] = Field(default_factory=list, description="e.g. admin, user, manager")
    has_auth: bool = False
    has_payments: bool = False
    has_admin_analytics: bool = False
    ambiguities: List[str] = Field(default_factory=list, description="Things the prompt left unclear")
    assumptions_made: List[str] = Field(default_factory=list, description="Reasonable defaults Claude filled in")
    raw_input: str = Field(..., description="Original user prompt, verbatim")

    class Config:
        extra = "forbid"