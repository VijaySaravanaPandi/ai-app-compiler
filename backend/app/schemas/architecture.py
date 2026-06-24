from pydantic import BaseModel, Field
from typing import List, Literal


class EntityField(BaseModel):
    name: str
    type: Literal["string", "integer", "float", "boolean", "date", "datetime", "enum", "reference"]
    required: bool = True
    enum_values: List[str] = Field(default_factory=list)

    class Config:
        extra = "ignore"


class EntityRelation(BaseModel):
    target_entity: str
    relation_type: Literal["one_to_one", "one_to_many", "many_to_one", "many_to_many"]
    via_field: str

    class Config:
        extra = "ignore"


class Entity(BaseModel):
    name: str
    fields: List[EntityField]
    relations: List[EntityRelation] = Field(default_factory=list)

    class Config:
        extra = "ignore"


class Role(BaseModel):
    name: str
    description: str = ""
    permissions: List[str] = Field(default_factory=list)

    class Config:
        extra = "ignore"


class Flow(BaseModel):
    name: str
    steps: List[str]
    triggered_by_role: str = "any"

    class Config:
        extra = "ignore"


class ArchitectureSchema(BaseModel):
    """Output of Stage 2 — System Design Layer."""

    entities: List[Entity]
    roles: List[Role]
    flows: List[Flow] = Field(default_factory=list)
    pages_needed: List[str] = Field(default_factory=list)

    class Config:
        extra = "ignore"