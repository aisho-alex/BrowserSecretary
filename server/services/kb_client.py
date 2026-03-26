"""Knowledge Base Client - wrapper for kb_mcp database operations."""
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import sqlite3

# Add knowledge_base_mcp to path
kb_path = Path(__file__).parent.parent.parent / "knowledge_base_mcp" / "src"
if kb_path.exists():
    sys.path.insert(0, str(kb_path))


class KnowledgeBaseClient:
    """Client for Knowledge Base MCP database operations."""
    
    def __init__(self, db_path: Path = None, data_dir: Path = None):
        self.db_path = Path(db_path) if db_path else Path("data/kb.db")
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn
    
    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        
        # Projects table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # FTS5 for projects
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS projects_fts USING fts5(
                name, description, content='projects', content_rowid='rowid'
            )
        """)
        
        # Knowledge entries table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_url TEXT,
                page_url TEXT,
                page_title TEXT,
                selection TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # FTS5 for knowledge
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                title, content, content='knowledge_entries', content_rowid='rowid'
            )
        """)
        
        # Tags table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#808080'
            )
        """)
        
        # Entry-Tags junction table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entry_tags (
                entry_id TEXT REFERENCES knowledge_entries(id) ON DELETE CASCADE,
                tag_id TEXT REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (entry_id, tag_id)
            )
        """)
        
        # Knowledge relations for graph
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_relations (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
                target_id TEXT NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
                relation_type TEXT DEFAULT 'related_to',
                weight REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_id, target_id, relation_type)
            )
        """)
        
        conn.commit()
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    # =========================================================================
    # PROJECTS
    # =========================================================================
    
    def list_projects(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all projects."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        return [dict(row) for row in rows]
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        return dict(row) if row else None
    
    def create_project(self, name: str, description: str = None) -> Dict[str, Any]:
        """Create a new project."""
        conn = self._get_conn()
        project_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, name, description, now, now)
        )
        conn.commit()
        return self.get_project(project_id)
    
    def update_project(self, project_id: str, name: str = None, description: str = None) -> Optional[Dict[str, Any]]:
        """Update project."""
        conn = self._get_conn()
        updates = []
        params = []
        if name:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(project_id)
            conn.execute(f"UPDATE projects SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        return self.get_project(project_id)
    
    def delete_project(self, project_id: str) -> bool:
        """Delete project."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def search_projects(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search projects."""
        conn = self._get_conn()
        safe_query = query.replace('"', '""').replace("'", "''")
        
        try:
            rows = conn.execute("""
                SELECT p.* FROM projects p
                JOIN projects_fts fts ON p.rowid = fts.rowid
                WHERE projects_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, [f'"{safe_query}"', limit]).fetchall()
        except Exception as e:
            # Fallback to LIKE search
            print(f"FTS5 search failed for projects: {e}")
            like_param = f"%{query}%"
            rows = conn.execute(
                "SELECT * FROM projects WHERE name LIKE ? OR description LIKE ? LIMIT ?",
                [like_param, like_param, limit]
            ).fetchall()
        
        return [dict(row) for row in rows]
    
    # =========================================================================
    # KNOWLEDGE ENTRIES
    # =========================================================================
    
    def _get_entry_tags(self, entry_id: str) -> List[str]:
        """Get tags for entry."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT t.name FROM tags t
            JOIN entry_tags et ON t.id = et.tag_id
            WHERE et.entry_id = ?
        """, (entry_id,)).fetchall()
        return [r[0] for r in rows]
    
    def _set_entry_tags(self, entry_id: str, tags: List[str]):
        """Set tags for entry."""
        conn = self._get_conn()
        conn.execute("DELETE FROM entry_tags WHERE entry_id = ?", (entry_id,))
        for tag_name in tags:
            row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
            if row:
                tag_id = row[0]
            else:
                tag_id = str(uuid4())
                conn.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (tag_id, tag_name))
            conn.execute("INSERT OR IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?, ?)", (entry_id, tag_id))
    
    def list_knowledge(
        self, 
        project_id: str = None, 
        tags: List[str] = None, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List knowledge entries."""
        conn = self._get_conn()
        query = "SELECT DISTINCT ke.* FROM knowledge_entries ke"
        joins = []
        where = []
        params = []
        
        if tags:
            joins.append("JOIN entry_tags et ON ke.id = et.entry_id")
            joins.append("JOIN tags t ON et.tag_id = t.id")
            placeholders = ",".join("?" * len(tags))
            where.append(f"t.name IN ({placeholders})")
            params.extend(tags)
        
        if project_id:
            where.append("ke.project_id = ?")
            params.append(project_id)
        
        if joins:
            query += " " + " ".join(joins)
        if where:
            query += " WHERE " + " AND ".join(where)
        
        query += " ORDER BY ke.updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        entries = []
        for row in rows:
            entry = dict(row)
            entry["tags"] = self._get_entry_tags(entry["id"])
            entries.append(entry)
        return entries
    
    def get_knowledge(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get knowledge entry by ID."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM knowledge_entries WHERE id = ?", (entry_id,)).fetchone()
        if row:
            entry = dict(row)
            entry["tags"] = self._get_entry_tags(entry["id"])
            return entry
        return None
    
    def create_knowledge(
        self,
        project_id: str,
        title: str,
        content: str,
        source_url: str = None,
        page_url: str = None,
        page_title: str = None,
        selection: str = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Create knowledge entry."""
        conn = self._get_conn()
        entry_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        
        conn.execute("""
            INSERT INTO knowledge_entries 
            (id, project_id, title, content, source_url, page_url, page_title, selection, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, project_id, title, content, source_url, page_url, page_title, selection, now, now))
        
        if tags:
            self._set_entry_tags(entry_id, tags)
        
        conn.commit()
        return self.get_knowledge(entry_id)
    
    def update_knowledge(
        self,
        entry_id: str,
        title: str = None,
        content: str = None,
        tags: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update knowledge entry."""
        conn = self._get_conn()
        updates = []
        params = []
        
        if title:
            updates.append("title = ?")
            params.append(title)
        if content:
            updates.append("content = ?")
            params.append(content)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(entry_id)
            conn.execute(f"UPDATE knowledge_entries SET {', '.join(updates)} WHERE id = ?", params)
        
        if tags is not None:
            self._set_entry_tags(entry_id, tags)
        
        conn.commit()
        return self.get_knowledge(entry_id)
    
    def delete_knowledge(self, entry_id: str) -> bool:
        """Delete knowledge entry."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM knowledge_entries WHERE id = ?", (entry_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def search_knowledge(self, query: str, project_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search in knowledge entries."""
        conn = self._get_conn()
        
        # Escape special FTS5 characters and build safe query
        # FTS5 requires escaping: ' " ( ) * ^ ~
        safe_query = query.replace('"', '""').replace("'", "''")
        
        try:
            sql = """
                SELECT ke.* FROM knowledge_entries ke
                JOIN knowledge_fts fts ON ke.rowid = fts.rowid
                WHERE knowledge_fts MATCH ?
            """
            params = [f'"{safe_query}"']  # Wrap in quotes for phrase search
            if project_id:
                sql += " AND ke.project_id = ?"
                params.append(project_id)
            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
        except Exception as e:
            # Fallback to LIKE search if FTS5 fails
            print(f"FTS5 search failed, falling back to LIKE: {e}")
            sql = "SELECT * FROM knowledge_entries WHERE title LIKE ? OR content LIKE ?"
            like_param = f"%{query}%"
            params = [like_param, like_param]
            if project_id:
                sql += " AND project_id = ?"
                params.append(project_id)
            sql += " LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
        
        entries = []
        for row in rows:
            entry = dict(row)
            entry["tags"] = self._get_entry_tags(entry["id"])
            entries.append(entry)
        return entries
    
    def unified_search(self, query: str, project_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Unified search across all entities."""
        results = []
        
        # Search knowledge
        knowledge = self.search_knowledge(query, project_id, limit)
        for entry in knowledge:
            results.append({
                "type": "knowledge",
                "id": entry["id"],
                "title": entry["title"],
                "snippet": entry["content"][:150] + "...",
                "tags": entry["tags"],
                "project_id": entry["project_id"]
            })
        
        # Search projects
        projects = self.search_projects(query, limit)
        for project in projects:
            results.append({
                "type": "project",
                "id": project["id"],
                "title": project["name"],
                "snippet": project.get("description", "")[:150],
                "tags": [],
                "project_id": project["id"]
            })
        
        return results[:limit]
    
    # =========================================================================
    # TAGS
    # =========================================================================
    
    def list_tags(self) -> List[Dict[str, Any]]:
        """List all tags."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
        return [dict(row) for row in rows]
    
    def get_or_create_tag(self, name: str, color: str = "#808080") -> Dict[str, Any]:
        """Get or create tag."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM tags WHERE name = ?", (name,)).fetchone()
        if row:
            return dict(row)
        tag_id = str(uuid4())
        conn.execute("INSERT INTO tags (id, name, color) VALUES (?, ?, ?)", (tag_id, name, color))
        conn.commit()
        return {"id": tag_id, "name": name, "color": color}
    
    def delete_tag(self, tag_id: str) -> bool:
        """Delete tag."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    # =========================================================================
    # GRAPH / RELATIONS
    # =========================================================================
    
    def add_relation(
        self, 
        source_id: str, 
        target_id: str, 
        relation_type: str = "related_to",
        weight: float = 1.0
    ) -> Dict[str, Any]:
        """Add relation between knowledge entries."""
        conn = self._get_conn()
        relation_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        
        conn.execute("""
            INSERT OR REPLACE INTO knowledge_relations 
            (id, source_id, target_id, relation_type, weight, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (relation_id, source_id, target_id, relation_type, weight, now))
        conn.commit()
        
        return {
            "id": relation_id,
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
            "weight": weight
        }
    
    def remove_relation(self, source_id: str, target_id: str, relation_type: str = None) -> bool:
        """Remove relation."""
        conn = self._get_conn()
        if relation_type:
            cursor = conn.execute(
                "DELETE FROM knowledge_relations WHERE source_id = ? AND target_id = ? AND relation_type = ?",
                (source_id, target_id, relation_type)
            )
        else:
            cursor = conn.execute(
                "DELETE FROM knowledge_relations WHERE source_id = ? AND target_id = ?",
                (source_id, target_id)
            )
        conn.commit()
        return cursor.rowcount > 0
    
    def get_graph(self, project_id: str = None, max_nodes: int = 100) -> Dict[str, Any]:
        """Get knowledge graph data for visualization."""
        conn = self._get_conn()
        
        # Get nodes (knowledge entries)
        if project_id:
            rows = conn.execute(
                "SELECT * FROM knowledge_entries WHERE project_id = ? LIMIT ?",
                (project_id, max_nodes)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM knowledge_entries LIMIT ?", (max_nodes,)
            ).fetchall()
        
        nodes = []
        node_ids = set()
        for row in rows:
            entry = dict(row)
            entry["tags"] = self._get_entry_tags(entry["id"])
            nodes.append({
                "id": entry["id"],
                "label": entry["title"][:50],
                "title": entry["title"],
                "tags": entry["tags"],
                "project_id": entry["project_id"]
            })
            node_ids.add(entry["id"])
        
        # Get edges (relations)
        placeholders = ",".join("?" * len(node_ids)) if node_ids else "''"
        edges_rows = conn.execute(f"""
            SELECT * FROM knowledge_relations 
            WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})
        """, list(node_ids) + list(node_ids)).fetchall()
        
        edges = []
        for row in edges_rows:
            edge = dict(row)
            edges.append({
                "source": edge["source_id"],
                "target": edge["target_id"],
                "type": edge["relation_type"],
                "weight": edge["weight"]
            })
        
        return {"nodes": nodes, "edges": edges}
