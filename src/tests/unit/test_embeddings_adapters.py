"""
Unit tests for Embeddings adapters (OpenAI, Google).
"""
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_settings():
    return MagicMock(
        openai_embedding_model="text-embedding-3-small",
        openai_api_key="sk-x",
        google_embedding_model="models/embedding-001",
        google_api_key="g-x",
    )


class TestOpenAIEmbeddingsAdapter:
    """Tests for OpenAIEmbeddingsAdapter."""

    def test_constructor_passes_settings(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.openai_embeddings.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.openai_embeddings.OpenAIEmbeddings"
        ) as cls:
            from src.infrastructure.adapters.openai_embeddings import (
                OpenAIEmbeddingsAdapter,
            )

            OpenAIEmbeddingsAdapter()
            cls.assert_called_once_with(
                model="text-embedding-3-small",
                openai_api_key="sk-x",
            )

    def test_embed_documents_delegates(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.openai_embeddings.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.openai_embeddings.OpenAIEmbeddings"
        ) as cls:
            cls.return_value.embed_documents.return_value = [[0.1, 0.2]]
            from src.infrastructure.adapters.openai_embeddings import (
                OpenAIEmbeddingsAdapter,
            )

            adapter = OpenAIEmbeddingsAdapter()
            out = adapter.embed_documents(["a", "b"])
            assert out == [[0.1, 0.2]]
            cls.return_value.embed_documents.assert_called_once_with(["a", "b"])

    def test_embed_query_delegates(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.openai_embeddings.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.openai_embeddings.OpenAIEmbeddings"
        ) as cls:
            cls.return_value.embed_query.return_value = [0.5]
            from src.infrastructure.adapters.openai_embeddings import (
                OpenAIEmbeddingsAdapter,
            )

            adapter = OpenAIEmbeddingsAdapter()
            assert adapter.embed_query("q") == [0.5]
            cls.return_value.embed_query.assert_called_once_with("q")

    def test_get_langchain_embeddings_returns_underlying(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.openai_embeddings.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.openai_embeddings.OpenAIEmbeddings"
        ) as cls:
            cls.return_value = "fake-emb"
            from src.infrastructure.adapters.openai_embeddings import (
                OpenAIEmbeddingsAdapter,
            )

            assert OpenAIEmbeddingsAdapter().get_langchain_embeddings() == "fake-emb"


class TestGoogleEmbeddingsAdapter:
    """Tests for GoogleEmbeddingsAdapter."""

    def test_constructor_passes_settings(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.google_embeddings.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.google_embeddings.GoogleGenerativeAIEmbeddings"
        ) as cls:
            from src.infrastructure.adapters.google_embeddings import (
                GoogleEmbeddingsAdapter,
            )

            GoogleEmbeddingsAdapter()
            cls.assert_called_once_with(
                model="models/embedding-001",
                google_api_key="g-x",
            )

    def test_embed_documents_delegates(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.google_embeddings.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.google_embeddings.GoogleGenerativeAIEmbeddings"
        ) as cls:
            cls.return_value.embed_documents.return_value = [[0.9]]
            from src.infrastructure.adapters.google_embeddings import (
                GoogleEmbeddingsAdapter,
            )

            assert GoogleEmbeddingsAdapter().embed_documents(["x"]) == [[0.9]]

    def test_embed_query_delegates(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.google_embeddings.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.google_embeddings.GoogleGenerativeAIEmbeddings"
        ) as cls:
            cls.return_value.embed_query.return_value = [0.3]
            from src.infrastructure.adapters.google_embeddings import (
                GoogleEmbeddingsAdapter,
            )

            assert GoogleEmbeddingsAdapter().embed_query("q") == [0.3]

    def test_get_langchain_embeddings_returns_underlying(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.google_embeddings.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.google_embeddings.GoogleGenerativeAIEmbeddings"
        ) as cls:
            cls.return_value = "fake-google-emb"
            from src.infrastructure.adapters.google_embeddings import (
                GoogleEmbeddingsAdapter,
            )

            assert (
                GoogleEmbeddingsAdapter().get_langchain_embeddings()
                == "fake-google-emb"
            )
