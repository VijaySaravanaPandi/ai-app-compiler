from pydantic import BaseModel, Field
from typing import List, Optional


class BusinessRule(BaseModel):
    name: str
    condition: str
    action: str
    applies_to_role: str = "any"
    description: Optional[str] = None
    trigger: Optional[str] = None
    affected_roles: Optional[List[str]] = None

    class Config:
        extra = "ignore"


class BusinessLogicSchema(BaseModel):
    """Output of Stage 3e — Business logic generation."""

    rules: List[BusinessRule]

    class Config:
        extra = "ignore"