from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Column(BaseModel):
    name: str
    type: Literal["TEXT", "INTEGER", "REAL", "BOOLEAN", "DATETIME"]
    primary_key: bool = False
    foreign_key: Optional[str] = Field(None, description="e.g. 'users.id'")
    nullable: bool = True
    required: bool = False
    unique: bool = False

    class Config:
        extra = "ignore"


class Table(BaseModel):
    name: str
    columns: List[Column]

    class Config:
        extra = "ignore"


class DBSchema(BaseModel):
    """Output of Stage 3c — DB schema generation."""

    tables: List[Table]

    class Config:
        extra = "ignore"