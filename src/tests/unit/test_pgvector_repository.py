"""
Unit tests for PGVectorRepository.

PGVector itself is mocked — we validate that the adapter correctly
delegates to it and contains the workaround for the langchain-postgres
session bug.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from langchain_core.documents import Document as LangchainDocument

from src.domain.entities.document import DocumentChunk
from src.domain.ports.embeddings import EmbeddingsPort


@pytest.fixture
def fake_embeddings():
    mock = Mock(spec=EmbeddingsPort)
    mock.get_langchain_embeddings.return_value = MagicMock(name="lc_embeddings")
    return mock


@pytest.fixture
def repository(fake_embeddings):
    """Build PGVectorRepository with PGVector class patched."""
    with patch(
        "src.infrastructure.adapters.pgvector_repository.PGVector"
    ) as pgv_cls:
        instance = MagicMock(name="pgvector_instance")
        # session_maker default; specific tests can override.
        instance.session_maker = MagicMock(name="session_maker")
        pgv_cls.return_value = instance
        from src.infrastructure.adapters.pgvector_repository import (
            PGVectorRepository,
        )
        repo = PGVectorRepository(fake_embeddings)
        repo._pgv_cls = pgv_cls  # expose for assertions
        yield repo


class TestConstruction:
    """Tests for PGVectorRepository.__init__."""

    def test_constructs_pgvector_with_settings(self, repository, fake_embeddings):
        """PGVector should be built with collection_name, connection, embeddings."""
        pgv_cls = repository._pgv_cls
        pgv_cls.assert_called_once()
        kwargs = pgv_cls.call_args.kwargs
        assert "collection_name" in kwargs
        assert "connection" in kwargs
        # connection must be the SQLAlchemy URL (postgresql+psycopg://...)
        assert "postgresql" in kwargs["connection"]
        assert kwargs["embeddings"] is fake_embeddings.get_langchain_embeddings.return_value


class TestResetSession:
    """Regression tests for the langchain-postgres session bug workaround."""

    def test_reset_session_calls_session_maker_remove(self, repository):
        repository._reset_session()
        repository._vectorstore.session_maker.remove.assert_called_once()

    def test_reset_session_no_op_without_session_maker(self, repository):
        # Simulate older/newer langchain-postgres versions without session_maker.
        del repository._vectorstore.session_maker
        # Must not raise.
        repository._reset_session()


class TestAddDocuments:
    """Tests for add_documents()."""

    def test_add_without_clear_calls_reset_session_and_add(self, repository):
        chunks = [
            DocumentChunk(content="A", metadata={"source_file": "f.pdf"}),
            DocumentChunk(content="B", metadata={"source_file": "f.pdf"}),
        ]
        n = repository.add_documents(chunks, clear_existing=False)

        # session reset must happen BEFORE add_documents (regression for bug).
        repository._vectorstore.session_maker.remove.assert_called_once()
        repository._vectorstore.add_documents.assert_called_once()
        passed = repository._vectorstore.add_documents.call_args.args[0]
        assert len(passed) == 2
        assert all(isinstance(d, LangchainDocument) for d in passed)
        assert passed[0].page_content == "A"
        assert passed[0].metadata == {"source_file": "f.pdf"}
        assert n == 2

    def test_add_with_clear_uses_from_documents_with_pre_delete(
        self, repository, fake_embeddings
    ):
        chunks = [DocumentChunk(content="X", metadata={"source_file": "x.pdf"})]
        pgv_cls = repository._pgv_cls
        # Reset call count from constructor.
        pgv_cls.from_documents = MagicMock(return_value=MagicMock())

        n = repository.add_documents(chunks, clear_existing=True)

        pgv_cls.from_documents.assert_called_once()
        kwargs = pgv_cls.from_documents.call_args.kwargs
        assert kwargs["pre_delete_collection"] is True
        assert kwargs["embedding"] is fake_embeddings.get_langchain_embeddings.return_value
        assert "collection_name" in kwargs
        assert "connection" in kwargs
        assert n == 1

    def test_add_empty_list_returns_zero(self, repository):
        assert repository.add_documents([], clear_existing=False) == 0

    def test_chunk_metadata_preserved(self, repository):
        chunks = [
            DocumentChunk(
                content="X",
                metadata={"source_file": "f.pdf", "page": 3, "extra": "y"},
            )
        ]
        repository.add_documents(chunks, clear_existing=False)
        passed = repository._vectorstore.add_documents.call_args.args[0]
        assert passed[0].metadata["page"] == 3
        assert passed[0].metadata["extra"] == "y"


class TestSearch:
    """Tests for search() — uses MMR for diversity."""

    def test_search_uses_mmr_with_fetch_k_3x(self, repository):
        repository._vectorstore.max_marginal_relevance_search.return_value = []
        repository.search("query", k=5)

        repository._vectorstore.max_marginal_relevance_search.assert_called_once_with(
            "query", k=5, fetch_k=15
        )

    def test_search_default_k(self, repository):
        repository._vectorstore.max_marginal_relevance_search.return_value = []
        repository.search("q")

        kwargs_or_args = repository._vectorstore.max_marginal_relevance_search.call_args
        assert kwargs_or_args.kwargs["k"] == 10
        assert kwargs_or_args.kwargs["fetch_k"] == 30

    def test_search_returns_document_chunks(self, repository):
        repository._vectorstore.max_marginal_relevance_search.return_value = [
            LangchainDocument(page_content="A", metadata={"source_file": "f.pdf"}),
            LangchainDocument(page_content="B", metadata={"source_file": "g.pdf"}),
        ]
        out = repository.search("q", k=2)

        assert len(out) == 2
        assert all(isinstance(c, DocumentChunk) for c in out)
        assert out[0].content == "A"
        assert out[0].metadata["source_file"] == "f.pdf"

    def test_search_empty_returns_empty(self, repository):
        repository._vectorstore.max_marginal_relevance_search.return_value = []
        assert repository.search("q") == []


class TestDeleteBySource:
    """Tests for delete_by_source() — raw SQL."""

    def _wire_engine(self, repository, collection_uuid="abc-uuid", rowcount=7):
        """Wire a fake engine onto the vectorstore. Returns conn mock."""
        fake_conn = MagicMock(name="conn")

        # First execute → fetchone returns (collection_uuid,) or None
        first_result = MagicMock()
        first_result.fetchone.return_value = (collection_uuid,) if collection_uuid else None
        # Second execute → DELETE returns object with rowcount
        second_result = MagicMock()
        second_result.rowcount = rowcount

        fake_conn.execute.side_effect = [first_result, second_result]

        ctx = MagicMock()
        ctx.__enter__.return_value = fake_conn
        ctx.__exit__.return_value = None

        engine = MagicMock(name="engine")
        engine.connect.return_value = ctx
        repository._vectorstore._engine = engine
        return fake_conn

    def test_delete_by_source_returns_rowcount(self, repository):
        conn = self._wire_engine(repository, collection_uuid="uuid-1", rowcount=5)
        n = repository.delete_by_source("doc.pdf")
        assert n == 5
        # Two execute calls: SELECT collection, DELETE rows
        assert conn.execute.call_count == 2
        conn.commit.assert_called_once()

    def test_delete_by_source_no_collection_returns_zero(self, repository):
        conn = self._wire_engine(repository, collection_uuid=None)
        n = repository.delete_by_source("doc.pdf")
        assert n == 0
        # Only the SELECT runs; no DELETE, no commit.
        assert conn.execute.call_count == 1
        conn.commit.assert_not_called()

    def test_delete_by_source_passes_source_file_param(self, repository):
        conn = self._wire_engine(repository, collection_uuid="x", rowcount=0)
        repository.delete_by_source("doc.pdf")
        # Second execute is the DELETE — its params must include source_file.
        delete_call = conn.execute.call_args_list[1]
        params = delete_call.args[1]
        assert params["source_file"] == "doc.pdf"
        assert params["collection_id"] == "x"


class TestGetRetriever:
    """Tests for get_retriever() — uses MMR."""

    def test_returns_mmr_retriever_with_fetch_k(self, repository):
        repository._vectorstore.as_retriever.return_value = "retriever"
        out = repository.get_retriever(k=7)

        assert out == "retriever"
        repository._vectorstore.as_retriever.assert_called_once_with(
            search_type="mmr",
            search_kwargs={"k": 7, "fetch_k": 21},
        )

    def test_default_k_is_ten(self, repository):
        repository.get_retriever()
        kwargs = repository._vectorstore.as_retriever.call_args.kwargs
        assert kwargs["search_kwargs"]["k"] == 10
        assert kwargs["search_kwargs"]["fetch_k"] == 30
