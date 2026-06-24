from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class RoleDef(BaseModel):
    name: str
    permissions: List[str]
    is_default: bool = False

    class Config:
        extra = "ignore"


class AuthSchema(BaseModel):
    """Output of Stage 3d — Auth schema generation."""

    method: Literal["jwt", "session"] = "jwt"
    roles: List[RoleDef]
    protected_routes: List[str] = Field(default_factory=list)
    jwt_strategy: Optional[str] = None
    token_expiry: Optional[str] = None
    login_field: Optional[str] = None

    class Config:
        extra = "ignore"