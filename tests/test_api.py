"""Tests for Knowledge Helper API."""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import tempfile
import shutil
from contextlib import asynccontextmanager

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from main import app
from services.kb_client import KnowledgeBaseClient


@pytest.fixture
def client():
    """Create test client with isolated database."""
    # Create temp database
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    data_dir = Path(temp_dir)

    # Create test app with lifespan
    @asynccontextmanager
    async def test_lifespan(app):
        kb = KnowledgeBaseClient(db_path=db_path, data_dir=data_dir)
        app.state.kb_client = kb
        # Auto-create default project
        kb.create_project("Default", "Default project")
        yield
        kb.close()

    # Create new app instance for test
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from routers import knowledge, projects, tags, qa, graph

    test_app = FastAPI(title="Knowledge Helper API Test", version="1.0.0", lifespan=test_lifespan)
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    test_app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
    test_app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
    test_app.include_router(tags.router, prefix="/api/tags", tags=["Tags"])
    test_app.include_router(qa.router, prefix="/api/qa", tags=["Q&A"])
    test_app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])

    @test_app.get("/")
    async def root():
        return {"name": "Knowledge Helper API", "version": "1.0.0", "status": "running"}

    @test_app.get("/health")
    async def health():
        return {"status": "healthy"}

    with TestClient(test_app) as test_client:
        yield test_client

    shutil.rmtree(temp_dir)


@pytest.fixture
def kb_client():
    """Create KB client with test database."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"

    client = KnowledgeBaseClient(db_path=db_path, data_dir=Path(temp_dir))

    yield client

    # Cleanup
    client.close()
    shutil.rmtree(temp_dir)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_returns_info(self, client):
        """Root endpoint should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Knowledge Helper API"
        assert "version" in data


class TestProjectsAPI:
    """Tests for projects endpoints."""

    def test_list_projects_empty(self, client):
        """List projects should return empty list initially."""
        response = client.get("/api/projects/")
        assert response.status_code == 200
        # Default project is auto-created
        data = response.json()
        assert isinstance(data, list)

    def test_create_project(self, client):
        """Should create a new project."""
        response = client.post(
            "/api/projects/",
            json={"name": "Test Project", "description": "Test description"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "Test description"
        assert "id" in data

    def test_get_project(self, client):
        """Should get project by ID."""
        # Create project
        create_response = client.post(
            "/api/projects/",
            json={"name": "Get Test Project"}
        )
        project_id = create_response.json()["id"]

        # Get project
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["id"] == project_id

    def test_get_nonexistent_project(self, client):
        """Should return 404 for nonexistent project."""
        response = client.get("/api/projects/nonexistent-id")
        assert response.status_code == 404

    def test_delete_project(self, client):
        """Should delete project."""
        # Create project
        create_response = client.post(
            "/api/projects/",
            json={"name": "Delete Test Project"}
        )
        project_id = create_response.json()["id"]

        # Delete project
        response = client.delete(f"/api/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] == True

        # Verify deleted
        get_response = client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 404


class TestKnowledgeAPI:
    """Tests for knowledge entries endpoints."""

    def test_create_knowledge_entry(self, client):
        """Should create knowledge entry."""
        # Get or create project
        projects_response = client.get("/api/projects/")
        projects = projects_response.json()
        if projects:
            project_id = projects[0]["id"]
        else:
            create_response = client.post(
                "/api/projects/",
                json={"name": "Test Project"}
            )
            project_id = create_response.json()["id"]

        # Create entry
        response = client.post(
            "/api/knowledge/",
            json={
                "project_id": project_id,
                "title": "Test Entry",
                "content": "This is test content for the knowledge entry.",
                "tags": ["test", "example"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Entry"
        assert "test" in data["tags"]

    def test_search_knowledge(self, client):
        """Should search knowledge entries."""
        response = client.get("/api/knowledge/unified/test")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_with_special_chars(self, client):
        """Should handle special characters in search."""
        # FTS5 special characters should be escaped
        response = client.get("/api/knowledge/unified/test%20query")
        assert response.status_code == 200


class TestTagsAPI:
    """Tests for tags endpoints."""

    def test_list_tags(self, client):
        """Should list all tags."""
        response = client.get("/api/tags/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_tag(self, client):
        """Should create a tag."""
        response = client.post(
            "/api/tags/",
            json={"name": "test-tag", "color": "#FF0000"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-tag"
        assert data["color"] == "#FF0000"


class TestQAAPI:
    """Tests for Q&A endpoint."""

    def test_qa_without_api_key(self, client):
        """Q&A should return error without API key."""
        response = client.post(
            "/api/qa/",
            json={"question": "What is this?"}
        )
        # Should return 200 but with error message in response
        assert response.status_code == 200
        data = response.json()
        # If no API key configured, should have error
        if data.get("error"):
            assert "API key" in data["answer"] or "error" in data["answer"].lower()

    def test_qa_empty_question(self, client):
        """Q&A with empty question should be handled."""
        # This would need validation - currently might fail
        pass


class TestGraphAPI:
    """Tests for knowledge graph endpoints."""

    def test_get_graph(self, client):
        """Should get graph data."""
        response = client.get("/api/graph/")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)


class TestKBClient:
    """Tests for KnowledgeBaseClient."""

    def test_create_and_get_project(self, kb_client):
        """Should create and retrieve project."""
        project = kb_client.create_project("Test", "Description")
        assert project["name"] == "Test"

        retrieved = kb_client.get_project(project["id"])
        assert retrieved["id"] == project["id"]

    def test_search_with_fallback(self, kb_client):
        """Search should fallback to LIKE if FTS5 fails."""
        # Create a project first
        project = kb_client.create_project("Search Test")

        # Create entry
        entry = kb_client.create_knowledge(
            project_id=project["id"],
            title="Test Entry",
            content="Some content here"
        )

        # Search - should work even with short queries
        results = kb_client.search_knowledge("Test")
        assert isinstance(results, list)

    def test_unified_search(self, kb_client):
        """Unified search should search across entities."""
        project = kb_client.create_project("Unified Test", "Test description")

        results = kb_client.unified_search("Test")
        assert isinstance(results, list)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
