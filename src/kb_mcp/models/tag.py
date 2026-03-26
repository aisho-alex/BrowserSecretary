"""Tag model."""
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Tag(BaseModel):
    """Tag model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=50)
    color: str = "#808080"
    
    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    """Model for creating a tag."""
    name: str = Field(..., min_length=1, max_length=50)
    color: str = "#808080"
