"""
Unit tests for domain entities.
"""
import pytest

from src.domain.entities.document import Document, DocumentChunk, SearchResult


class TestDocumentChunk:
    """Tests for DocumentChunk entity."""
    
    def test_create_chunk(self):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            content="Test content",
            metadata={"page": 1, "source_file": "test.pdf"}
        )
        
        assert chunk.content == "Test content"
        assert chunk.source_file == "test.pdf"
        assert chunk.page_number == 1
    
    def test_chunk_without_metadata(self):
        """Test chunk with empty metadata."""
        chunk = DocumentChunk(content="Test")
        
        assert chunk.source_file is None
        assert chunk.page_number is None


class TestDocument:
    """Tests for Document entity."""
    
    def test_create_document(self, sample_chunks):
        """Test creating a document."""
        doc = Document(name="test.pdf", chunks=sample_chunks)
        
        assert doc.name == "test.pdf"
        assert doc.chunk_count == 2
    
    def test_empty_document(self):
        """Test document with no chunks."""
        doc = Document(name="empty.pdf")
        
        assert doc.chunk_count == 0


class TestSearchResult:
    """Tests for SearchResult entity."""
    
    def test_create_search_result(self, sample_chunks):
        """Test creating a search result."""
        result = SearchResult(
            query="What is this?",
            answer="This is a test.",
            sources=sample_chunks
        )
        
        assert result.query == "What is this?"
        assert result.answer == "This is a test."
        assert len(result.sources) == 2
