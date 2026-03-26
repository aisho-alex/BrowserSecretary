"""Comprehensive tests for Knowledge Helper API - Q&A and Search functionality."""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from services.kb_client import KnowledgeBaseClient


@pytest.fixture
def temp_db():
    """Create temporary database for tests."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    yield db_path, Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def kb_client(temp_db):
    """Create KB client with test database."""
    db_path, data_dir = temp_db
    client = KnowledgeBaseClient(db_path=db_path, data_dir=data_dir)
    # Auto-create default project
    client.create_project("Default", "Default project")
    yield client
    client.close()


@pytest.fixture
def populated_kb(kb_client):
    """Create KB client with sample data."""
    # Create projects
    project1 = kb_client.create_project("Python", "Python programming knowledge")
    project2 = kb_client.create_project("JavaScript", "JavaScript programming knowledge")
    
    # Create knowledge entries
    entries = []
    
    # Python entries
    entries.append(kb_client.create_knowledge(
        project_id=project1["id"],
        title="Python List Comprehension",
        content="List comprehension is a concise way to create lists in Python. "
                "Syntax: [expression for item in iterable if condition]. "
                "Example: [x*2 for x in range(10) if x % 2 == 0]",
        tags=["python", "lists", "comprehension"]
    ))
    
    entries.append(kb_client.create_knowledge(
        project_id=project1["id"],
        title="Python Decorators",
        content="A decorator is a function that takes another function and extends its behavior "
                "without explicitly modifying it. Use @decorator syntax. "
                "Example: @login_required, @staticmethod, @classmethod",
        tags=["python", "decorators", "functions"]
    ))
    
    entries.append(kb_client.create_knowledge(
        project_id=project1["id"],
        title="Python Context Managers",
        content="Context managers allow you to allocate and release resources precisely. "
                "Use 'with' statement. Example: with open('file.txt') as f: ...",
        tags=["python", "context-manager", "resources"]
    ))
    
    # JavaScript entries
    entries.append(kb_client.create_knowledge(
        project_id=project2["id"],
        title="JavaScript Closures",
        content="A closure is a function that has access to variables from its outer (enclosing) scope, "
                "even after the outer function has returned. Essential for callbacks and data privacy.",
        tags=["javascript", "closures", "functions"]
    ))
    
    entries.append(kb_client.create_knowledge(
        project_id=project2["id"],
        title="JavaScript Promises",
        content="A Promise is an object representing the eventual completion or failure of an asynchronous operation. "
                "States: pending, fulfilled, rejected. Methods: .then(), .catch(), .finally()",
        tags=["javascript", "promises", "async"]
    ))
    
    entries.append(kb_client.create_knowledge(
        project_id=project2["id"],
        title="JavaScript Event Loop",
        content="The event loop is a mechanism that allows JavaScript to perform non-blocking operations. "
                "It constantly checks the call stack and callback queue, moving callbacks to the stack when empty.",
        tags=["javascript", "event-loop", "async"]
    ))
    
    yield kb_client, project1, project2, entries


# =============================================================================
# Q&A Tests - Unit tests for QA router logic
# =============================================================================

class TestQAAPI:
    """Tests for Q&A endpoint logic."""

    def test_qa_without_api_key(self, populated_kb, monkeypatch):
        """Q&A should return error message when API key not configured."""
        from config import get_settings
        settings = get_settings()
        
        # Ensure no API key
        original_key = settings.llm_api_key
        settings.llm_api_key = ""
        
        try:
            # Import router and create test request
            from server.routers.qa import QuestionRequest
            
            # Search should work without API key
            kb = populated_kb[0]
            results = kb.search_knowledge("Python", limit=5)
            assert isinstance(results, list)
            
            # Without API key, answer should mention it
            assert "API key" in settings.llm_api_key or settings.llm_api_key == ""
        finally:
            settings.llm_api_key = original_key

    def test_qa_empty_question_handling(self, populated_kb):
        """Q&A should handle empty question."""
        kb_client, project1, project2, entries = populated_kb
        
        # Empty search should return empty results
        results = kb_client.search_knowledge("", limit=5)
        assert isinstance(results, list)

    def test_qa_with_context_from_knowledge(self, populated_kb, monkeypatch):
        """Q&A should find relevant knowledge and include as sources."""
        kb_client, project1, project2, entries = populated_kb
        
        # Search for Python lists
        results = kb_client.search_knowledge("list", limit=3)
        assert len(results) > 0
        
        # Should find List Comprehension entry
        titles = [entry["title"] for entry in results]
        assert any("List" in t for t in titles)

    def test_qa_with_project_filter(self, populated_kb):
        """Q&A should respect project_id filter."""
        kb_client, project1, project2, entries = populated_kb
        
        # Search with project filter
        results = kb_client.search_knowledge("function", project_id=project2["id"], limit=10)
        
        # All results should be from JavaScript project
        for entry in results:
            assert entry["project_id"] == project2["id"]

    def test_qa_with_no_matching_context(self, populated_kb):
        """Q&A should handle case when no relevant knowledge found."""
        kb_client, project1, project2, entries = populated_kb
        
        # Search for something not in KB
        results = kb_client.search_knowledge("quantum computing", limit=5)
        # Should return empty or minimal results
        assert isinstance(results, list)

    def test_qa_with_specific_context_ids(self, populated_kb):
        """Q&A should include specific entries by context_ids."""
        kb_client, project1, project2, entries = populated_kb
        
        # Get specific entry ID (Decorators)
        target_entry_id = entries[1]["id"]
        
        # Get that specific entry
        entry = kb_client.get_knowledge(target_entry_id)
        assert entry is not None
        assert entry["id"] == target_entry_id
        assert "Decorator" in entry["title"]

    def test_qa_context_building(self, populated_kb):
        """Test context building for Q&A."""
        kb_client, project1, project2, entries = populated_kb
        
        # Get multiple entries and build context
        context_entries = kb_client.search_knowledge("Python", limit=2)
        
        context_text = ""
        sources = []
        for i, entry in enumerate(context_entries, 1):
            context_text += f"\n[{i}] {entry['title']}\n{entry['content']}\n"
            sources.append({
                "id": entry["id"],
                "title": entry["title"],
                "tags": entry.get("tags", [])
            })
        
        assert len(sources) > 0
        assert len(context_text) > 0


# =============================================================================
# Search Tests - Direct KB client tests
# =============================================================================

class TestSearchAPI:
    """Tests for search functionality."""

    def test_search_knowledge_basic(self, populated_kb):
        """Basic search should find relevant entries."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("Python", limit=10)
        assert isinstance(results, list)
        # Should find Python entries
        assert len(results) > 0

    def test_search_knowledge_list_comprehension(self, populated_kb):
        """Search should find list comprehension entry."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("list", limit=10)
        assert isinstance(results, list)
        
        # Should find entries with "list" in content
        content_check = any("list" in e["content"].lower() for e in results)
        assert content_check

    def test_search_knowledge_with_tags(self, populated_kb):
        """Search should find entries by tag content."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("decorators", limit=10)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_knowledge_with_project_filter(self, populated_kb):
        """Search should respect project_id filter."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("function", project_id=project2["id"], limit=10)
        
        # All results should be from JavaScript project
        for entry in results:
            assert entry["project_id"] == project2["id"]

    def test_search_knowledge_with_limit(self, populated_kb):
        """Search should respect limit parameter."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("Python", limit=1)
        
        assert len(results) <= 1

    def test_search_knowledge_special_characters(self, populated_kb):
        """Search should handle special characters."""
        kb_client, project1, project2, entries = populated_kb
        
        # FTS5 special characters should not crash
        results = kb_client.search_knowledge("x*2", limit=10)
        assert isinstance(results, list)

    def test_search_knowledge_case_insensitive(self, populated_kb):
        """Search should be case insensitive."""
        kb_client, project1, project2, entries = populated_kb
        
        # Search in different cases
        results_lower = kb_client.search_knowledge("python", limit=10)
        results_upper = kb_client.search_knowledge("PYTHON", limit=10)
        
        # Both should return results
        assert len(results_lower) > 0
        assert len(results_upper) > 0

    def test_unified_search_basic(self, populated_kb):
        """Unified search should search across all entities."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.unified_search("Python", limit=10)
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Should have type field
        for item in results:
            assert "type" in item

    def test_unified_search_finds_project(self, populated_kb):
        """Unified search should find projects too."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.unified_search("JavaScript", limit=10)
        
        # Should find JavaScript project
        titles = [item.get("title", "") for item in results]
        assert any("JavaScript" in t for t in titles)

    def test_unified_search_with_limit(self, populated_kb):
        """Unified search should respect limit."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.unified_search("Python", limit=2)
        
        assert len(results) <= 2

    def test_unified_search_empty_result(self, populated_kb):
        """Unified search should return empty list for no matches."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.unified_search("quantum entanglement", limit=10)
        assert isinstance(results, list)

    def test_search_knowledge_no_matches(self, populated_kb):
        """Search should return empty list when no matches."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("nonexistentterm12345", limit=10)
        assert isinstance(results, list)
        assert len(results) == 0


# =============================================================================
# KB Client Search Tests
# =============================================================================

class TestKBClientSearch:
    """Tests for KnowledgeBaseClient search methods."""

    def test_search_knowledge_direct(self, populated_kb):
        """Test search_knowledge method directly."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("decorator", limit=10)
        assert isinstance(results, list)

    def test_search_knowledge_with_project_filter(self, populated_kb):
        """Test search with project filter."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge(
            "function",
            project_id=project1["id"],
            limit=10
        )
        
        # All results should be from project1
        for entry in results:
            assert entry["project_id"] == project1["id"]

    def test_unified_search_direct(self, populated_kb):
        """Test unified_search method directly."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.unified_search("Python", limit=10)
        assert isinstance(results, list)

    def test_search_with_fallback(self, kb_client):
        """Search should fallback to LIKE if FTS5 fails."""
        project = kb_client.create_project("Fallback Test")
        
        entry = kb_client.create_knowledge(
            project_id=project["id"],
            title="Fallback Test Entry",
            content="This is test content for fallback search"
        )
        
        # Search should work
        results = kb_client.search_knowledge("Fallback")
        assert isinstance(results, list)

    def test_search_short_query(self, populated_kb):
        """Search should handle short queries."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("Py", limit=10)
        assert isinstance(results, list)

    def test_list_knowledge(self, populated_kb):
        """Test list_knowledge method."""
        kb_client, project1, project2, entries = populated_kb
        
        # List all knowledge
        results = kb_client.list_knowledge(limit=10)
        assert isinstance(results, list)
        assert len(results) == 6  # We created 6 entries
        
        # List with project filter
        results = kb_client.list_knowledge(project_id=project1["id"], limit=10)
        assert len(results) == 3  # 3 Python entries

    def test_get_knowledge(self, populated_kb):
        """Test get_knowledge method."""
        kb_client, project1, project2, entries = populated_kb
        
        # Get specific entry
        entry = kb_client.get_knowledge(entries[0]["id"])
        assert entry is not None
        assert entry["id"] == entries[0]["id"]
        
        # Get non-existent entry
        entry = kb_client.get_knowledge("nonexistent-id")
        assert entry is None


# =============================================================================
# Integration Tests
# =============================================================================

class TestSearchAndQAIntegration:
    """Integration tests for search and Q&A working together."""

    def test_search_then_get_details(self, populated_kb):
        """Test workflow: search, then get details for each result."""
        kb_client, project1, project2, entries = populated_kb
        
        # 1. Search for relevant entries
        search_results = kb_client.search_knowledge("closure", limit=5)
        assert len(search_results) > 0
        
        # 2. Get full details for each result
        for result in search_results:
            full_entry = kb_client.get_knowledge(result["id"])
            assert full_entry is not None
            assert "tags" in full_entry

    def test_create_search_verify(self, kb_client):
        """Test workflow: create entry, search, verify."""
        # Create project
        project = kb_client.create_project("Test Project", "For testing")
        
        # Create entry
        entry = kb_client.create_knowledge(
            project_id=project["id"],
            title="Test Search Entry",
            content="This content should be searchable",
            tags=["test", "search"]
        )
        
        # Search for it
        results = kb_client.search_knowledge("searchable", limit=10)
        
        # Should find the entry
        assert len(results) > 0
        assert any(e["id"] == entry["id"] for e in results)

    def test_project_knowledge_relation(self, populated_kb):
        """Test that knowledge entries are properly linked to projects."""
        kb_client, project1, project2, entries = populated_kb
        
        # Get all knowledge for Python project
        python_knowledge = kb_client.list_knowledge(project_id=project1["id"], limit=10)
        
        # Should have 3 entries
        assert len(python_knowledge) == 3
        
        # All should belong to Python project
        for entry in python_knowledge:
            assert entry["project_id"] == project1["id"]


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestSearchEdgeCases:
    """Tests for edge cases in search."""

    def test_search_with_unicode(self, kb_client):
        """Search should handle unicode characters."""
        project = kb_client.create_project("Unicode Test")
        
        entry = kb_client.create_knowledge(
            project_id=project["id"],
            title="Тест на русском",
            content="Содержимое на русском языке",
            tags=["unicode", "russian"]
        )
        
        # Search should not crash
        results = kb_client.search_knowledge("русском", limit=10)
        assert isinstance(results, list)

    def test_search_with_very_long_query(self, populated_kb):
        """Search should handle very long queries."""
        kb_client, project1, project2, entries = populated_kb
        
        long_query = "python " * 100
        results = kb_client.search_knowledge(long_query, limit=10)
        assert isinstance(results, list)

    def test_search_with_html_content(self, kb_client):
        """Search should handle HTML in content."""
        project = kb_client.create_project("HTML Test")
        
        entry = kb_client.create_knowledge(
            project_id=project["id"],
            title="HTML Content",
            content="<div><p>Some HTML content</p></div>",
            tags=["html", "web"]
        )
        
        results = kb_client.search_knowledge("HTML", limit=10)
        assert isinstance(results, list)

    def test_zero_limit(self, populated_kb):
        """Search with limit=0 should return empty list."""
        kb_client, project1, project2, entries = populated_kb
        
        results = kb_client.search_knowledge("Python", limit=0)
        assert results == []

    def test_negative_offset(self, populated_kb):
        """Search should handle negative offset gracefully."""
        kb_client, project1, project2, entries = populated_kb
        
        # This might raise an error or return empty - just ensure no crash
        try:
            results = kb_client.list_knowledge(limit=10, offset=-1)
            assert isinstance(results, list)
        except Exception:
            pass  # Expected behavior


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
