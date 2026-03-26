"""Requirement service."""
from typing import List, Optional
import sqlite3

from kb_mcp.models.requirement import Requirement, RequirementCreate, RequirementUpdate
from kb_mcp.db.repositories import RequirementRepository


class RequirementService:
    """Service for requirement operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.repo = RequirementRepository(conn)
    
    def create(self, data: RequirementCreate) -> Requirement:
        """Create a new requirement."""
        return self.repo.create(data)
    
    def get(self, requirement_id: str) -> Optional[Requirement]:
        """Get a requirement by ID."""
        return self.repo.get(requirement_id)
    
    def list(self, project_id: str, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 100) -> List[Requirement]:
        """List requirements for a project."""
        return self.repo.list(project_id, status, priority, limit)
    
    def update(self, requirement_id: str, data: RequirementUpdate) -> Optional[Requirement]:
        """Update a requirement."""
        return self.repo.update(requirement_id, data)
    
    def delete(self, requirement_id: str) -> bool:
        """Delete a requirement."""
        return self.repo.delete(requirement_id)
    
    def search(self, query: str, project_id: Optional[str] = None, limit: int = 20) -> List[Requirement]:
        """Search requirements."""
        return self.repo.search(query, project_id, limit)
