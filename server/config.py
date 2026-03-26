"""Server configuration with environment variables."""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment."""
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    
    # Knowledge Base
    kb_db_path: Path = Path("data/kb.db")
    kb_data_dir: Path = Path("data")
    
    # LLM Configuration
    llm_api_url: str = "https://api.openai.com/v1/chat/completions"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    
    # CORS
    cors_origins: str = "chrome-extension://*,moz-extension://*"
    
    # Graph
    graph_max_nodes: int = 100
    graph_max_edges: int = 200
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins as list."""
        return [o.strip() for o in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
