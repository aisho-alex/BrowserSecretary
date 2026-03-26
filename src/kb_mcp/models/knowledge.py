"""Knowledge entry model."""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from pydantic import BaseModel, Field


class KnowledgeEntry(BaseModel):
    """Knowledge entry model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    requirement_id: Optional[str] = None
    project_id: str
    title: str
    content: str
    source_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class KnowledgeCreate(BaseModel):
    """Model for creating a knowledge entry."""
    requirement_id: Optional[str] = None
    project_id: str
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class KnowledgeUpdate(BaseModel):
    """Model for updating a knowledge entry."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    source_url: Optional[str] = None
    tags: Optional[List[str]] = None
