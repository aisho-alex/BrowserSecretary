"""MCP tools definitions."""
from typing import List, Optional, Dict, Any
import json

from kb_mcp.db import get_db
from kb_mcp.services import ProjectService, RequirementService, KnowledgeService, SearchService
from kb_mcp.models import ProjectCreate, ProjectUpdate, RequirementCreate, RequirementUpdate, KnowledgeCreate, KnowledgeUpdate


# ============================================================================
# PROJECT TOOLS
# ============================================================================

async def projects_list(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """List all projects."""
    db = get_db()
    conn = db.connect()
    try:
        svc = ProjectService(conn)
        projects = svc.list(limit, offset)
        return [{"id": p.id, "name": p.name, "description": p.description, "created_at": str(p.created_at)} for p in projects]
    finally:
        db.close()


async def project_create(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Create a new project."""
    db = get_db()
    conn = db.connect()
    try:
        svc = ProjectService(conn)
        project = svc.create(ProjectCreate(name=name, description=description))
        conn.commit()
        return {"id": project.id, "name": project.name, "description": project.description, "created_at": str(project.created_at)}
    finally:
        db.close()


async def project_get(project_id: str) -> Optional[Dict[str, Any]]:
    """Get a project by ID."""
    db = get_db()
    conn = db.connect()
    try:
        svc = ProjectService(conn)
        project = svc.get(project_id)
        if project:
            return {"id": project.id, "name": project.name, "description": project.description, "created_at": str(project.created_at), "updated_at": str(project.updated_at)}
        return None
    finally:
        db.close()


async def project_update(project_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a project."""
    db = get_db()
    conn = db.connect()
    try:
        svc = ProjectService(conn)
        project = svc.update(project_id, ProjectUpdate(name=name, description=description))
        conn.commit()
        if project:
            return {"id": project.id, "name": project.name, "description": project.description}
        return None
    finally:
        db.close()


async def project_delete(project_id: str) -> bool:
    """Delete a project."""
    db = get_db()
    conn = db.connect()
    try:
        svc = ProjectService(conn)
        result = svc.delete(project_id)
        conn.commit()
        return result
    finally:
        db.close()


async def project_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search projects by name/description."""
    db = get_db()
    conn = db.connect()
    try:
        svc = ProjectService(conn)
        projects = svc.search(query, limit)
        return [{"id": p.id, "name": p.name, "description": p.description} for p in projects]
    finally:
        db.close()


# ============================================================================
# REQUIREMENT TOOLS
# ============================================================================

async def requirements_list(project_id: str, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """List requirements for a project."""
    db = get_db()
    conn = db.connect()
    try:
        svc = RequirementService(conn)
        reqs = svc.list(project_id, status, priority, limit)
        return [{"id": r.id, "project_id": r.project_id, "title": r.title, "content": r.content, "priority": r.priority.value, "status": r.status.value} for r in reqs]
    finally:
        db.close()


async def requirement_create(project_id: str, title: str, content: str, priority: str = "medium") -> Dict[str, Any]:
    """Create a new requirement."""
    db = get_db()
    conn = db.connect()
    try:
        svc = RequirementService(conn)
        from kb_mcp.models.requirement import Priority
        req = svc.create(RequirementCreate(project_id=project_id, title=title, content=content, priority=Priority(priority)))
        conn.commit()
        return {"id": req.id, "project_id": req.project_id, "title": req.title, "priority": req.priority.value, "status": req.status.value}
    finally:
        db.close()


async def requirement_get(requirement_id: str) -> Optional[Dict[str, Any]]:
    """Get a requirement by ID."""
    db = get_db()
    conn = db.connect()
    try:
        svc = RequirementService(conn)
        req = svc.get(requirement_id)
        if req:
            return {"id": req.id, "project_id": req.project_id, "title": req.title, "content": req.content, "priority": req.priority.value, "status": req.status.value}
        return None
    finally:
        db.close()


async def requirement_update(requirement_id: str, title: Optional[str] = None, content: Optional[str] = None, priority: Optional[str] = None, status: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a requirement."""
    db = get_db()
    conn = db.connect()
    try:
        svc = RequirementService(conn)
        from kb_mcp.models.requirement import Priority, Status as ReqStatus
        upd = RequirementUpdate(
            title=title,
            content=content,
            priority=Priority(priority) if priority else None,
            status=ReqStatus(status) if status else None
        )
        req = svc.update(requirement_id, upd)
        conn.commit()
        if req:
            return {"id": req.id, "title": req.title, "status": req.status.value, "priority": req.priority.value}
        return None
    finally:
        db.close()


async def requirement_delete(requirement_id: str) -> bool:
    """Delete a requirement."""
    db = get_db()
    conn = db.connect()
    try:
        svc = RequirementService(conn)
        result = svc.delete(requirement_id)
        conn.commit()
        return result
    finally:
        db.close()


# ============================================================================
# KNOWLEDGE TOOLS
# ============================================================================

async def knowledge_list(project_id: Optional[str] = None, requirement_id: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """List knowledge entries."""
    db = get_db()
    conn = db.connect()
    try:
        svc = KnowledgeService(conn)
        entries = svc.list(project_id, requirement_id, tags, limit)
        return [{"id": e.id, "project_id": e.project_id, "title": e.title, "content": e.content[:100] + "...", "tags": e.tags} for e in entries]
    finally:
        db.close()


async def knowledge_create(project_id: str, title: str, content: str, requirement_id: Optional[str] = None, source_url: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a new knowledge entry."""
    db = get_db()
    conn = db.connect()
    try:
        svc = KnowledgeService(conn)
        entry = svc.create(KnowledgeCreate(
            project_id=project_id,
            title=title,
            content=content,
            requirement_id=requirement_id,
            source_url=source_url,
            tags=tags or []
        ))
        conn.commit()
        return {"id": entry.id, "title": entry.title, "tags": entry.tags}
    finally:
        db.close()


async def knowledge_get(entry_id: str) -> Optional[Dict[str, Any]]:
    """Get a knowledge entry by ID."""
    db = get_db()
    conn = db.connect()
    try:
        svc = KnowledgeService(conn)
        entry = svc.get(entry_id)
        if entry:
            return {"id": entry.id, "project_id": entry.project_id, "title": entry.title, "content": entry.content, "source_url": entry.source_url, "tags": entry.tags}
        return None
    finally:
        db.close()


async def knowledge_update(entry_id: str, title: Optional[str] = None, content: Optional[str] = None, tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Update a knowledge entry."""
    db = get_db()
    conn = db.connect()
    try:
        svc = KnowledgeService(conn)
        entry = svc.update(entry_id, KnowledgeUpdate(title=title, content=content, tags=tags))
        conn.commit()
        if entry:
            return {"id": entry.id, "title": entry.title, "tags": entry.tags}
        return None
    finally:
        db.close()


async def knowledge_delete(entry_id: str) -> bool:
    """Delete a knowledge entry."""
    db = get_db()
    conn = db.connect()
    try:
        svc = KnowledgeService(conn)
        result = svc.delete(entry_id)
        conn.commit()
        return result
    finally:
        db.close()


async def knowledge_search(query: str, project_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Full-text search in knowledge entries."""
    db = get_db()
    conn = db.connect()
    try:
        svc = KnowledgeService(conn)
        entries = svc.search(query, project_id, limit)
        return [{"id": e.id, "title": e.title, "content": e.content[:150] + "...", "tags": e.tags} for e in entries]
    finally:
        db.close()


# ============================================================================
# UNIFIED SEARCH
# ============================================================================

async def unified_search(query: str, project_id: Optional[str] = None, entity_types: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Unified search across all entities (projects, requirements, knowledge)."""
    db = get_db()
    conn = db.connect()
    try:
        svc = SearchService(conn)
        results = svc.search(query, project_id, entity_types, limit)
        return [r.to_dict() for r in results]
    finally:
        db.close()


# ============================================================================
# TAG TOOLS
# ============================================================================

async def tags_list() -> List[Dict[str, Any]]:
    """List all tags."""
    db = get_db()
    conn = db.connect()
    try:
        from kb_mcp.db.repositories import TagRepository
        from kb_mcp.models import TagCreate
        repo = TagRepository(conn)
        tags = repo.list()
        return [{"id": t.id, "name": t.name, "color": t.color} for t in tags]
    finally:
        db.close()


# Export all tools as a list for MCP server
MCP_TOOLS = {
    "projects_list": projects_list,
    "project_create": project_create,
    "project_get": project_get,
    "project_update": project_update,
    "project_delete": project_delete,
    "project_search": project_search,
    "requirements_list": requirements_list,
    "requirement_create": requirement_create,
    "requirement_get": requirement_get,
    "requirement_update": requirement_update,
    "requirement_delete": requirement_delete,
    "knowledge_list": knowledge_list,
    "knowledge_create": knowledge_create,
    "knowledge_get": knowledge_get,
    "knowledge_update": knowledge_update,
    "knowledge_delete": knowledge_delete,
    "knowledge_search": knowledge_search,
    "unified_search": unified_search,
    "tags_list": tags_list,
}
