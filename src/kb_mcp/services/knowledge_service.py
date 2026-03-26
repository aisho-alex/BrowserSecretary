"""Knowledge service."""
from typing import List, Optional
import sqlite3

from kb_mcp.models.knowledge import KnowledgeEntry, KnowledgeCreate, KnowledgeUpdate
from kb_mcp.db.repositories import KnowledgeRepository


class KnowledgeService:
    """Service for knowledge entry operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.repo = KnowledgeRepository(conn)
    
    def create(self, data: KnowledgeCreate) -> KnowledgeEntry:
        """Create a new knowledge entry."""
        return self.repo.create(data)
    
    def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a knowledge entry by ID."""
        return self.repo.get(entry_id)
    
    def list(self, project_id: str = None, requirement_id: str = None, tags: List[str] = None, limit: int = 100) -> List[KnowledgeEntry]:
        """List knowledge entries."""
        return self.repo.list(project_id, requirement_id, tags, limit)
    
    def update(self, entry_id: str, data: KnowledgeUpdate) -> Optional[KnowledgeEntry]:
        """Update a knowledge entry."""
        return self.repo.update(entry_id, data)
    
    def delete(self, entry_id: str) -> bool:
        """Delete a knowledge entry."""
        return self.repo.delete(entry_id)
    
    def search(self, query: str, project_id: str = None, limit: int = 20) -> List[KnowledgeEntry]:
        """Search knowledge entries."""
        return self.repo.search(query, project_id, limit)
