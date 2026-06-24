from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class FieldValidation(BaseModel):
    field: str
    rule: str

    class Config:
        extra = "forbid"


class Endpoint(BaseModel):
    path: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    request_fields: List[str] = Field(default_factory=list)
    response_fields: List[str] = Field(default_factory=list)
    auth_required: bool = True
    allowed_roles: List[str] = Field(default_factory=lambda: ["any"])
    validations: List[FieldValidation] = Field(default_factory=list)
    maps_to_entity: Optional[str] = None

    class Config:
        extra = "forbid"


class APISchema(BaseModel):
    """Output of Stage 3b — API schema generation."""

    endpoints: List[Endpoint]

    class Config:
        extra = "forbid"