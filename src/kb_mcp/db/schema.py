"""Database schema initialization with FTS5."""
import sqlite3


def init_schema(conn: sqlite3.Connection):
    """Initialize database schema."""
    cursor = conn.cursor()
    
    # Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # FTS5 index for projects
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS projects_fts USING fts5(
            name, description, content='projects', content_rowid='rowid'
        )
    """)
    
    # Triggers for projects FTS
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS projects_ai AFTER INSERT ON projects BEGIN
            INSERT INTO projects_fts(rowid, name, description) VALUES (new.rowid, new.name, new.description);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS projects_ad AFTER DELETE ON projects BEGIN
            INSERT INTO projects_fts(projects_fts, rowid, name, description) VALUES('delete', old.rowid, old.name, old.description);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS projects_au AFTER UPDATE ON projects BEGIN
            INSERT INTO projects_fts(projects_fts, rowid, name, description) VALUES('delete', old.rowid, old.name, old.description);
            INSERT INTO projects_fts(rowid, name, description) VALUES (new.rowid, new.name, new.description);
        END
    """)
    
    # Requirements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requirements (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # FTS5 index for requirements
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS requirements_fts USING fts5(
            title, content, content='requirements', content_rowid='rowid'
        )
    """)
    
    # Triggers for requirements FTS
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS requirements_ai AFTER INSERT ON requirements BEGIN
            INSERT INTO requirements_fts(rowid, title, content) VALUES (new.rowid, new.title, new.content);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS requirements_ad AFTER DELETE ON requirements BEGIN
            INSERT INTO requirements_fts(requirements_fts, rowid, title, content) VALUES('delete', old.rowid, old.title, old.content);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS requirements_au AFTER UPDATE ON requirements BEGIN
            INSERT INTO requirements_fts(requirements_fts, rowid, title, content) VALUES('delete', old.rowid, old.title, old.content);
            INSERT INTO requirements_fts(rowid, title, content) VALUES (new.rowid, new.title, new.content);
        END
    """)
    
    # Knowledge entries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_entries (
            id TEXT PRIMARY KEY,
            requirement_id TEXT REFERENCES requirements(id) ON DELETE SET NULL,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # FTS5 index for knowledge entries
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            title, content, content='knowledge_entries', content_rowid='rowid'
        )
    """)
    
    # Triggers for knowledge FTS
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge_entries BEGIN
            INSERT INTO knowledge_fts(rowid, title, content) VALUES (new.rowid, new.title, new.content);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge_entries BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content) VALUES('delete', old.rowid, old.title, old.content);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge_entries BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content) VALUES('delete', old.rowid, old.title, old.content);
            INSERT INTO knowledge_fts(rowid, title, content) VALUES (new.rowid, new.title, new.content);
        END
    """)
    
    # Tags table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#808080'
        )
    """)
    
    # Entry-Tags junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entry_tags (
            entry_id TEXT REFERENCES knowledge_entries(id) ON DELETE CASCADE,
            tag_id TEXT REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (entry_id, tag_id)
        )
    """)
    
    conn.commit()
