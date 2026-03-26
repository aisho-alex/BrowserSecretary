"""Knowledge Helper Server - FastAPI Application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import knowledge, projects, tags, qa, graph
from services.kb_client import KnowledgeBaseClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    settings = get_settings()
    
    # Initialize KB client
    kb_client = KnowledgeBaseClient(
        db_path=settings.kb_db_path,
        data_dir=settings.kb_data_dir
    )
    app.state.kb_client = kb_client
    
    # Auto-create default project if not exists
    existing = kb_client.list_projects(limit=1)
    if not existing:
        kb_client.create_project("Default", "Default project for quick saves")
        print("✅ Created 'Default' project")
    
    yield
    
    # Cleanup
    kb_client.close()


app = FastAPI(
    title="Knowledge Helper API",
    description="Browser extension backend for knowledge management with MCP integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for browser extension - must be added BEFORE other middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",  # Allow all origins (extensions, localhost, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])
app.include_router(qa.router, prefix="/api/qa", tags=["Q&A"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Knowledge Helper API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
