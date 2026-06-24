from pydantic import BaseModel, Field
from typing import List


class BusinessRule(BaseModel):
    name: str
    condition: str
    action: str
    applies_to_role: str = "any"

    class Config:
        extra = "forbid"


class BusinessLogicSchema(BaseModel):
    """Output of Stage 3e — Business logic generation."""

    rules: List[BusinessRule]

    class Config:
        extra = "forbid"