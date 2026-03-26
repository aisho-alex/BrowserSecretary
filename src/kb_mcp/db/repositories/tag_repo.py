"""Repository for tags."""
from typing import List, Optional
import sqlite3
from uuid import uuid4

from kb_mcp.models.tag import Tag, TagCreate


class TagRepository:
    """Repository for tag CRUD operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def create(self, data: TagCreate) -> Tag:
        """Create a new tag."""
        tag = Tag(name=data.name, color=data.color)
        self.conn.execute(
            "INSERT INTO tags (id, name, color) VALUES (?, ?, ?)",
            (tag.id, tag.name, tag.color)
        )
        return tag
    
    def get(self, tag_id: str) -> Optional[Tag]:
        """Get tag by ID."""
        row = self.conn.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
        return Tag(**dict(row)) if row else None
    
    def get_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name."""
        row = self.conn.execute("SELECT * FROM tags WHERE name = ?", (name,)).fetchone()
        return Tag(**dict(row)) if row else None
    
    def list(self) -> List[Tag]:
        """List all tags."""
        rows = self.conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
        return [Tag(**dict(row)) for row in rows]
    
    def delete(self, tag_id: str) -> bool:
        """Delete a tag."""
        cursor = self.conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        return cursor.rowcount > 0
