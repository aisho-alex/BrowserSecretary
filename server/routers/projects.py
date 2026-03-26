"""Projects API router."""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("/")
async def list_projects(request: Request, limit: int = 50, offset: int = 0):
    """List all projects."""
    kb = request.app.state.kb_client
    return kb.list_projects(limit, offset)


@router.get("/{project_id}")
async def get_project(project_id: str, request: Request):
    """Get project by ID."""
    kb = request.app.state.kb_client
    project = kb.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/")
async def create_project(data: ProjectCreate, request: Request):
    """Create new project."""
    kb = request.app.state.kb_client
    return kb.create_project(data.name, data.description)


@router.patch("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, request: Request):
    """Update project."""
    kb = request.app.state.kb_client
    project = kb.update_project(project_id, data.name, data.description)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, request: Request):
    """Delete project."""
    kb = request.app.state.kb_client
    if not kb.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True}


@router.get("/search/{query}")
async def search_projects(query: str, request: Request, limit: int = 10):
    """Search projects."""
    kb = request.app.state.kb_client
    return kb.search_projects(query, limit)
