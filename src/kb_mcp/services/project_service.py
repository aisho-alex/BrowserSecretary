"""Project service."""
from typing import List, Optional
import sqlite3

from kb_mcp.models.project import Project, ProjectCreate, ProjectUpdate
from kb_mcp.db.repositories import ProjectRepository


class ProjectService:
    """Service for project operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.repo = ProjectRepository(conn)
    
    def create(self, data: ProjectCreate) -> Project:
        """Create a new project."""
        return self.repo.create(data)
    
    def get(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self.repo.get(project_id)
    
    def list(self, limit: int = 100, offset: int = 0) -> List[Project]:
        """List all projects."""
        return self.repo.list(limit, offset)
    
    def update(self, project_id: str, data: ProjectUpdate) -> Optional[Project]:
        """Update a project."""
        return self.repo.update(project_id, data)
    
    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        return self.repo.delete(project_id)
    
    def search(self, query: str, limit: int = 20) -> List[Project]:
        """Search projects."""
        return self.repo.search(query, limit)
