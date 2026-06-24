from pydantic import BaseModel, Field
from typing import List, Literal


class RoleDef(BaseModel):
    name: str
    permissions: List[str]

    class Config:
        extra = "forbid"


class AuthSchema(BaseModel):
    """Output of Stage 3d — Auth schema generation."""

    method: Literal["jwt", "session"] = "jwt"
    roles: List[RoleDef]
    protected_routes: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"