"""Search service - unified search across all entities."""
from typing import List, Dict, Any, Optional
import sqlite3

from kb_mcp.services.project_service import ProjectService
from kb_mcp.services.requirement_service import RequirementService
from kb_mcp.services.knowledge_service import KnowledgeService


class SearchResult:
    """Search result container."""
    def __init__(self, entity_type: str, entity_id: str, title: str, content: str, project_id: str = None, score: float = 0.0):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.title = title
        self.content = content
        self.project_id = project_id
        self.score = score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.entity_type,
            "id": self.entity_id,
            "title": self.title,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "project_id": self.project_id,
            "score": round(self.score, 2),
        }


class SearchService:
    """Unified search service across all knowledge base entities."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.project_svc = ProjectService(conn)
        self.requirement_svc = RequirementService(conn)
        self.knowledge_svc = KnowledgeService(conn)
    
    def search(self, query: str, project_id: str = None, entity_types: List[str] = None, limit: int = 20) -> List[SearchResult]:
        """
        Search across all entities.
        
        Args:
            query: Search query string
            project_id: Optional filter by project
            entity_types: List of entity types to search ('project', 'requirement', 'knowledge')
            limit: Maximum results
        
        Returns:
            List of SearchResult objects
        """
        results = []
        
        if entity_types is None or 'project' in entity_types:
            for p in self.project_svc.search(query, limit):
                results.append(SearchResult(
                    entity_type='project',
                    entity_id=p.id,
                    title=p.name,
                    content=p.description or '',
                    score=1.0  # FTS5 rank
                ))
        
        if entity_types is None or 'requirement' in entity_types:
            for r in self.requirement_svc.search(query, project_id, limit):
                results.append(SearchResult(
                    entity_type='requirement',
                    entity_id=r.id,
                    title=r.title,
                    content=r.content,
                    project_id=r.project_id,
                    score=1.0
                ))
        
        if entity_types is None or 'knowledge' in entity_types:
            for k in self.knowledge_svc.search(query, project_id, limit):
                results.append(SearchResult(
                    entity_type='knowledge',
                    entity_id=k.id,
                    title=k.title,
                    content=k.content,
                    project_id=k.project_id,
                    score=1.0
                ))
        
        # Sort by relevance and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
