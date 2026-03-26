"""Repository for requirements."""
from typing import List, Optional
import sqlite3
from datetime import datetime

from kb_mcp.models.requirement import Requirement, RequirementCreate, RequirementUpdate, Status


class RequirementRepository:
    """Repository for requirement CRUD operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def create(self, data: RequirementCreate) -> Requirement:
        """Create a new requirement."""
        req = Requirement(
            project_id=data.project_id,
            title=data.title,
            content=data.content,
            priority=data.priority,
        )
        self.conn.execute(
            "INSERT INTO requirements (id, project_id, title, content, priority, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (req.id, req.project_id, req.title, req.content, req.priority.value, req.status.value, req.created_at, req.updated_at)
        )
        return req
    
    def get(self, requirement_id: str) -> Optional[Requirement]:
        """Get requirement by ID."""
        row = self.conn.execute("SELECT * FROM requirements WHERE id = ?", (requirement_id,)).fetchone()
        if row:
            d = dict(row)
            d['priority'] = d['priority']
            d['status'] = d['status']
            return Requirement(**d)
        return None
    
    def list(self, project_id: str, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 100) -> List[Requirement]:
        """List requirements for a project."""
        query = "SELECT * FROM requirements WHERE project_id = ?"
        params = [project_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(query, params).fetchall()
        return [Requirement(**dict(row)) for row in rows]
    
    def update(self, requirement_id: str, data: RequirementUpdate) -> Optional[Requirement]:
        """Update a requirement."""
        updates = []
        params = []
        if data.title is not None:
            updates.append("title = ?")
            params.append(data.title)
        if data.content is not None:
            updates.append("content = ?")
            params.append(data.content)
        if data.priority is not None:
            updates.append("priority = ?")
            params.append(data.priority.value)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status.value)
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow())
            params.append(requirement_id)
            self.conn.execute(f"UPDATE requirements SET {', '.join(updates)} WHERE id = ?", params)
        return self.get(requirement_id)
    
    def delete(self, requirement_id: str) -> bool:
        """Delete a requirement."""
        cursor = self.conn.execute("DELETE FROM requirements WHERE id = ?", (requirement_id,))
        return cursor.rowcount > 0
    
    def search(self, query: str, project_id: Optional[str] = None, limit: int = 20) -> List[Requirement]:
        """Full-text search in requirements."""
        sql = """
            SELECT r.* FROM requirements r
            JOIN requirements_fts fts ON r.rowid = fts.rowid
            WHERE requirements_fts MATCH ?
        """
        params = [query]
        if project_id:
            sql += " AND r.project_id = ?"
            params.append(project_id)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [Requirement(**dict(row)) for row in rows]
