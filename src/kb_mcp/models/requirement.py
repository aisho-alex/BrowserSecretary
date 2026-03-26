"""Requirement model."""
from datetime import datetime
from typing import Optional
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Requirement priority."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Requirement status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class Requirement(BaseModel):
    """Requirement model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    title: str
    content: str
    priority: Priority = Priority.MEDIUM
    status: Status = Status.OPEN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class RequirementCreate(BaseModel):
    """Model for creating a requirement."""
    project_id: str
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    priority: Priority = Priority.MEDIUM


class RequirementUpdate(BaseModel):
    """Model for updating a requirement."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    priority: Optional[Priority] = None
    status: Optional[Status] = None
