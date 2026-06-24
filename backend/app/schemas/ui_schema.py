from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Component(BaseModel):
    type: Literal["table", "form", "card", "chart", "button", "nav", "text", "list"]
    name: str
    props: dict = Field(default_factory=dict)
    api_binding: Optional[str] = Field(None, description="API endpoint path this component reads/writes")

    class Config:
        extra = "ignore"


class Page(BaseModel):
    name: str
    route: str
    components: List[Component]
    layout: Literal["single_column", "sidebar", "grid", "split"] = "sidebar"
    access_roles: List[str] = Field(default_factory=lambda: ["any"])

    class Config:
        extra = "ignore"


class UISchema(BaseModel):
    """Output of Stage 3a — UI schema generation."""

    pages: List[Page]

    class Config:
        extra = "ignore"