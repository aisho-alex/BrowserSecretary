"""Repository for projects."""
from typing import List, Optional
import sqlite3
from datetime import datetime

from kb_mcp.models.project import Project, ProjectCreate, ProjectUpdate


class ProjectRepository:
    """Repository for project CRUD operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def create(self, data: ProjectCreate) -> Project:
        """Create a new project."""
        project = Project(name=data.name, description=data.description)
        self.conn.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (project.id, project.name, project.description, project.created_at, project.updated_at)
        )
        return project
    
    def get(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        row = self.conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        return Project(**dict(row)) if row else None
    
    def list(self, limit: int = 100, offset: int = 0) -> List[Project]:
        """List all projects."""
        rows = self.conn.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        return [Project(**dict(row)) for row in rows]
    
    def update(self, project_id: str, data: ProjectUpdate) -> Optional[Project]:
        """Update a project."""
        updates = []
        params = []
        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow())
            params.append(project_id)
            self.conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?", params
            )
        return self.get(project_id)
    
    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        cursor = self.conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cursor.rowcount > 0
    
    def search(self, query: str, limit: int = 20) -> List[Project]:
        """Full-text search in projects."""
        rows = self.conn.execute("""
            SELECT p.* FROM projects p
            JOIN projects_fts fts ON p.rowid = fts.rowid
            WHERE projects_fts MATCH ?
            ORDER BY rank LIMIT ?
        """, (query, limit)).fetchall()
        return [Project(**dict(row)) for row in rows]
