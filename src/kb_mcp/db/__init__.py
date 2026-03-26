"""Database package."""
from kb_mcp.db.database import Database, get_db
from kb_mcp.db.schema import init_schema

__all__ = ["Database", "get_db", "init_schema"]
