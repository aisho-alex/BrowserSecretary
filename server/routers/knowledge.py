"""Knowledge entries API router."""
from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


class KnowledgeCreate(BaseModel):
    project_id: str
    title: str
    content: str
    source_url: Optional[str] = None
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    selection: Optional[str] = None
    tags: Optional[List[str]] = None


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("/")
async def list_knowledge(
    request: Request,
    project_id: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List knowledge entries."""
    kb = request.app.state.kb_client
    tag_list = tags.split(",") if tags else None
    return kb.list_knowledge(project_id, tag_list, limit, offset)


@router.get("/{entry_id}")
async def get_knowledge(entry_id: str, request: Request):
    """Get knowledge entry."""
    kb = request.app.state.kb_client
    entry = kb.get_knowledge(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/")
async def create_knowledge(data: KnowledgeCreate, request: Request):
    """Create knowledge entry from browser extension."""
    kb = request.app.state.kb_client
    return kb.create_knowledge(
        project_id=data.project_id,
        title=data.title,
        content=data.content,
        source_url=data.source_url,
        page_url=data.page_url,
        page_title=data.page_title,
        selection=data.selection,
        tags=data.tags or []
    )


@router.patch("/{entry_id}")
async def update_knowledge(entry_id: str, data: KnowledgeUpdate, request: Request):
    """Update knowledge entry."""
    kb = request.app.state.kb_client
    entry = kb.update_knowledge(entry_id, data.title, data.content, data.tags)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/{entry_id}")
async def delete_knowledge(entry_id: str, request: Request):
    """Delete knowledge entry."""
    kb = request.app.state.kb_client
    if not kb.delete_knowledge(entry_id):
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"deleted": True}


@router.get("/search/{query}")
async def search_knowledge(query: str, request: Request, project_id: Optional[str] = None, limit: int = 20):
    """Full-text search in knowledge."""
    kb = request.app.state.kb_client
    return kb.search_knowledge(query, project_id, limit)


@router.get("/unified/{query}")
async def unified_search(query: str, request: Request, project_id: Optional[str] = None, limit: int = 10):
    """Unified search across all entities."""
    kb = request.app.state.kb_client
    return kb.unified_search(query, project_id, limit)
