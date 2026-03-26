"""Configuration for KB MCP Server."""
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""
    
    # Database
    db_path: Path = Path(os.getenv("KB_DB_PATH", "data/kb.db"))
    
    # MCP Server
    mcp_host: str = os.getenv("MCP_HOST", "0.0.0.0")
    mcp_port: int = int(os.getenv("MCP_PORT", "8080"))
    
    # Search
    search_limit_default: int = 20
    search_limit_max: int = 100
    
    # Data directory
    data_dir: Path = Path(os.getenv("KB_DATA_DIR", "data"))
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
