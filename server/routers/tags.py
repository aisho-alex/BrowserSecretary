"""Tags API router."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#808080"


@router.get("/")
async def list_tags(request=None):
    """List all tags."""
    kb = request.app.state.kb_client
    return kb.list_tags()


@router.post("/")
async def create_tag(data: TagCreate, request=None):
    """Create or get existing tag."""
    kb = request.app.state.kb_client
    return kb.get_or_create_tag(data.name, data.color)


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str, request=None):
    """Delete tag."""
    kb = request.app.state.kb_client
    if not kb.delete_tag(tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"deleted": True}
