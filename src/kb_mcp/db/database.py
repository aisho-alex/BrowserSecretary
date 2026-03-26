"""Database connection and management."""
import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

from kb_mcp.config import config
from kb_mcp.db.schema import init_schema


class Database:
    """SQLite database wrapper with FTS5 support."""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = None
    
    def connect(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
            # Initialize schema
            init_schema(self._connection)
        return self._connection
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def __enter__(self):
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connect().commit()
        return False


# Global database instance
_db: Database = None


def get_db() -> Database:
    """Get global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db


def close_db():
    """Close global database."""
    global _db
    if _db:
        _db.close()
        _db = None
