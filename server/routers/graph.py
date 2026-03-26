"""Knowledge Graph API router."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


class RelationCreate(BaseModel):
    source_id: str
    target_id: str
    relation_type: str = "related_to"
    weight: float = 1.0


@router.get("/")
async def get_graph(project_id: Optional[str] = None, max_nodes: int = 100, request=None):
    """Get knowledge graph data for visualization."""
    kb = request.app.state.kb_client
    return kb.get_graph(project_id, max_nodes)


@router.post("/relations")
async def add_relation(data: RelationCreate, request=None):
    """Add relation between knowledge entries."""
    kb = request.app.state.kb_client
    
    # Verify entries exist
    source = kb.get_knowledge(data.source_id)
    target = kb.get_knowledge(data.target_id)
    
    if not source:
        raise HTTPException(status_code=404, detail="Source entry not found")
    if not target:
        raise HTTPException(status_code=404, detail="Target entry not found")
    
    return kb.add_relation(
        data.source_id,
        data.target_id,
        data.relation_type,
        data.weight
    )


@router.delete("/relations")
async def remove_relation(
    source_id: str,
    target_id: str,
    relation_type: Optional[str] = None,
    request=None
):
    """Remove relation between entries."""
    kb = request.app.state.kb_client
    if not kb.remove_relation(source_id, target_id, relation_type):
        raise HTTPException(status_code=404, detail="Relation not found")
    return {"deleted": True}
