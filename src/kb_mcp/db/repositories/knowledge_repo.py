"""Repository for knowledge entries."""
from typing import List, Optional
import sqlite3
from datetime import datetime

from kb_mcp.models.knowledge import KnowledgeEntry, KnowledgeCreate, KnowledgeUpdate


class KnowledgeRepository:
    """Repository for knowledge entry CRUD operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def _get_tags(self, entry_id: str) -> List[str]:
        """Get tags for an entry."""
        rows = self.conn.execute("""
            SELECT t.name FROM tags t
            JOIN entry_tags et ON t.id = et.tag_id
            WHERE et.entry_id = ?
        """, (entry_id,)).fetchall()
        return [r[0] for r in rows]
    
    def _set_tags(self, entry_id: str, tags: List[str]):
        """Set tags for an entry."""
        # Remove existing tags
        self.conn.execute("DELETE FROM entry_tags WHERE entry_id = ?", (entry_id,))
        # Add new tags
        for tag_name in tags:
            # Get or create tag
            row = self.conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
            if row:
                tag_id = row[0]
            else:
                from uuid import uuid4
                tag_id = str(uuid4())
                self.conn.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (tag_id, tag_name))
            self.conn.execute("INSERT OR IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?, ?)", (entry_id, tag_id))
    
    def _row_to_entry(self, row: sqlite3.Row) -> KnowledgeEntry:
        """Convert row to KnowledgeEntry."""
        d = dict(row)
        d['tags'] = self._get_tags(d['id'])
        return KnowledgeEntry(**d)
    
    def create(self, data: KnowledgeCreate) -> KnowledgeEntry:
        """Create a new knowledge entry."""
        entry = KnowledgeEntry(
            project_id=data.project_id,
            requirement_id=data.requirement_id,
            title=data.title,
            content=data.content,
            source_url=data.source_url,
            tags=data.tags,
        )
        self.conn.execute(
            "INSERT INTO knowledge_entries (id, requirement_id, project_id, title, content, source_url, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (entry.id, entry.requirement_id, entry.project_id, entry.title, entry.content, entry.source_url, entry.created_at, entry.updated_at)
        )
        self._set_tags(entry.id, data.tags)
        return entry
    
    def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get knowledge entry by ID."""
        row = self.conn.execute("SELECT * FROM knowledge_entries WHERE id = ?", (entry_id,)).fetchone()
        return self._row_to_entry(row) if row else None
    
    def list(self, project_id: str = None, requirement_id: str = None, tags: List[str] = None, limit: int = 100) -> List[KnowledgeEntry]:
        """List knowledge entries."""
        query = "SELECT DISTINCT ke.* FROM knowledge_entries ke"
        joins = []
        where_clauses = []
        params = []
        
        if tags:
            joins.append("JOIN entry_tags et ON ke.id = et.entry_id")
            joins.append("JOIN tags t ON et.tag_id = t.id")
            placeholders = ",".join("?" * len(tags))
            where_clauses.append(f"t.name IN ({placeholders})")
            params.extend(tags)
        
        if project_id:
            where_clauses.append("ke.project_id = ?")
            params.append(project_id)
        
        if requirement_id:
            where_clauses.append("ke.requirement_id = ?")
            params.append(requirement_id)
        
        if joins:
            query += " " + " ".join(joins)
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY ke.updated_at DESC LIMIT ?"
        params.append(limit)
        
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_entry(row) for row in rows]
    
    def update(self, entry_id: str, data: KnowledgeUpdate) -> Optional[KnowledgeEntry]:
        """Update a knowledge entry."""
        updates = []
        params = []
        if data.title is not None:
            updates.append("title = ?")
            params.append(data.title)
        if data.content is not None:
            updates.append("content = ?")
            params.append(data.content)
        if data.source_url is not None:
            updates.append("source_url = ?")
            params.append(data.source_url)
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow())
            params.append(entry_id)
            self.conn.execute(f"UPDATE knowledge_entries SET {', '.join(updates)} WHERE id = ?", params)
        if data.tags is not None:
            self._set_tags(entry_id, data.tags)
        return self.get(entry_id)
    
    def delete(self, entry_id: str) -> bool:
        """Delete a knowledge entry."""
        cursor = self.conn.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry_id,))
        return cursor.rowcount > 0
    
    def search(self, query: str, project_id: str = None, limit: int = 20) -> List[KnowledgeEntry]:
        """Full-text search in knowledge entries."""
        sql = """
            SELECT ke.* FROM knowledge_entries ke
            JOIN knowledge_fts fts ON ke.rowid = fts.rowid
            WHERE knowledge_fts MATCH ?
        """
        params = [query]
        if project_id:
            sql += " AND ke.project_id = ?"
            params.append(project_id)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [self._row_to_entry(row) for row in rows]
