"""Projects API router."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from services.kb_client import KnowledgeBaseClient

router = APIRouter()


def get_kb(request) -> KnowledgeBaseClient:
    """Get KB client from app state."""
    return request.app.state.kb_client


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
async def list_projects(limit: int = 50, offset: int = 0, request=Depends(get_kb)):
    """List all projects."""
    kb = request.app.state.kb_client
    return kb.list_projects(limit, offset)


@router.get("/{project_id}")
async def get_project(project_id: str, request=Depends(get_kb)):
    """Get project by ID."""
    kb = request.app.state.kb_client
    project = kb.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/")
async def create_project(data: ProjectCreate, request=Depends(get_kb)):
    """Create new project."""
    kb = request.app.state.kb_client
    return kb.create_project(data.name, data.description)


@router.patch("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, request=Depends(get_kb)):
    """Update project."""
    kb = request.app.state.kb_client
    project = kb.update_project(project_id, data.name, data.description)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, request=Depends(get_kb)):
    """Delete project."""
    kb = request.app.state.kb_client
    if not kb.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True}


@router.get("/search/{query}")
async def search_projects(query: str, limit: int = 10, request=Depends(get_kb)):
    """Search projects."""
    kb = request.app.state.kb_client
    return kb.search_projects(query, limit)
