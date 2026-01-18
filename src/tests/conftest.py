"""
Test configuration and fixtures.
"""
import pytest
from unittest.mock import Mock, MagicMock

from src.domain.entities.document import Document, DocumentChunk, SearchResult
from src.domain.ports.embeddings import EmbeddingsPort
from src.domain.ports.llm import LLMPort
from src.domain.ports.repository import RepositoryPort


@pytest.fixture
def mock_embeddings() -> EmbeddingsPort:
    """Create mock embeddings port."""
    mock = Mock(spec=EmbeddingsPort)
    mock.embed_documents.return_value = [[0.1, 0.2, 0.3]]
    mock.embed_query.return_value = [0.1, 0.2, 0.3]
    return mock


@pytest.fixture
def mock_llm() -> LLMPort:
    """Create mock LLM port."""
    mock = Mock(spec=LLMPort)
    mock.generate.return_value = "Test response"
    return mock


@pytest.fixture
def mock_repository() -> RepositoryPort:
    """Create mock repository port."""
    mock = Mock(spec=RepositoryPort)
    mock.add_documents.return_value = 5
    mock.search.return_value = [
        DocumentChunk(content="Test content", metadata={"page": 1})
    ]
    mock.delete_by_source.return_value = 5
    return mock


@pytest.fixture
def sample_chunks() -> list[DocumentChunk]:
    """Create sample document chunks."""
    return [
        DocumentChunk(
            content="This is test content.",
            metadata={"page": 1, "source_file": "test.pdf"}
        ),
        DocumentChunk(
            content="More test content here.",
            metadata={"page": 2, "source_file": "test.pdf"}
        ),
    ]


@pytest.fixture
def sample_document(sample_chunks) -> Document:
    """Create sample document."""
    return Document(name="test.pdf", chunks=sample_chunks)
