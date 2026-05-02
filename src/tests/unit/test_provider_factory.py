"""
Unit tests for ProviderFactory.

The factory dispatches to OpenAI or Google adapters based on settings.
We patch the adapter classes so no real API client is constructed.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.domain.exceptions import ProviderNotConfiguredError
from src.infrastructure.factories.provider_factory import ProviderFactory


@pytest.fixture(autouse=True)
def reset_factory():
    """Ensure each test starts with a clean factory state."""
    ProviderFactory.reset()
    yield
    ProviderFactory.reset()


def _settings(**overrides):
    """Build a settings-like object with sane defaults."""
    defaults = {
        "llm_provider": "openai",
        "openai_api_key": "sk-test",
        "google_api_key": "g-test",
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


class TestGetEmbeddings:
    """Tests for get_embeddings() dispatch and validation."""

    def test_openai_provider_returns_openai_adapter(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai"),
        ), patch(
            "src.infrastructure.factories.provider_factory.OpenAIEmbeddingsAdapter"
        ) as adapter_cls:
            adapter_cls.return_value = "openai-emb"
            out = ProviderFactory.get_embeddings()
            assert out == "openai-emb"
            adapter_cls.assert_called_once()

    def test_google_provider_returns_google_adapter(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="google"),
        ), patch(
            "src.infrastructure.factories.provider_factory.GoogleEmbeddingsAdapter"
        ) as adapter_cls:
            adapter_cls.return_value = "google-emb"
            out = ProviderFactory.get_embeddings()
            assert out == "google-emb"

    def test_openai_missing_key_raises(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai", openai_api_key=None),
        ):
            with pytest.raises(ProviderNotConfiguredError, match="OpenAI"):
                ProviderFactory.get_embeddings()

    def test_google_missing_key_raises(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="google", google_api_key=None),
        ):
            with pytest.raises(ProviderNotConfiguredError, match="Google"):
                ProviderFactory.get_embeddings()

    def test_unknown_provider_raises(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="cohere"),
        ):
            with pytest.raises(ProviderNotConfiguredError, match="Unknown provider"):
                ProviderFactory.get_embeddings()

    def test_singleton(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai"),
        ), patch(
            "src.infrastructure.factories.provider_factory.OpenAIEmbeddingsAdapter"
        ) as adapter_cls:
            adapter_cls.return_value = MagicMock()
            a = ProviderFactory.get_embeddings()
            b = ProviderFactory.get_embeddings()
            assert a is b
            adapter_cls.assert_called_once()


class TestGetLLM:
    """Tests for get_llm() dispatch and validation."""

    def test_openai_provider_returns_openai_adapter(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai"),
        ), patch(
            "src.infrastructure.factories.provider_factory.OpenAILLMAdapter"
        ) as adapter_cls:
            adapter_cls.return_value = "openai-llm"
            assert ProviderFactory.get_llm() == "openai-llm"

    def test_google_provider_returns_google_adapter(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="google"),
        ), patch(
            "src.infrastructure.factories.provider_factory.GoogleLLMAdapter"
        ) as adapter_cls:
            adapter_cls.return_value = "google-llm"
            assert ProviderFactory.get_llm() == "google-llm"

    def test_openai_missing_key_raises(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai", openai_api_key=""),
        ):
            with pytest.raises(ProviderNotConfiguredError, match="OpenAI"):
                ProviderFactory.get_llm()

    def test_google_missing_key_raises(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="google", google_api_key=""),
        ):
            with pytest.raises(ProviderNotConfiguredError, match="Google"):
                ProviderFactory.get_llm()

    def test_unknown_provider_raises(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="bedrock"),
        ):
            with pytest.raises(ProviderNotConfiguredError, match="Unknown provider"):
                ProviderFactory.get_llm()

    def test_singleton(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai"),
        ), patch(
            "src.infrastructure.factories.provider_factory.OpenAILLMAdapter"
        ) as adapter_cls:
            adapter_cls.return_value = MagicMock()
            assert ProviderFactory.get_llm() is ProviderFactory.get_llm()
            adapter_cls.assert_called_once()


class TestGetRepository:
    """Tests for get_repository() — composes embeddings + PGVector."""

    def test_chains_embeddings_into_repository(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai"),
        ), patch(
            "src.infrastructure.factories.provider_factory.OpenAIEmbeddingsAdapter"
        ) as emb_cls, patch(
            "src.infrastructure.factories.provider_factory.PGVectorRepository"
        ) as repo_cls:
            emb_cls.return_value = "emb"
            repo_cls.return_value = "repo"

            out = ProviderFactory.get_repository()
            assert out == "repo"
            repo_cls.assert_called_once_with("emb")

    def test_singleton(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai"),
        ), patch(
            "src.infrastructure.factories.provider_factory.OpenAIEmbeddingsAdapter"
        ), patch(
            "src.infrastructure.factories.provider_factory.PGVectorRepository"
        ) as repo_cls:
            repo_cls.return_value = MagicMock()
            assert ProviderFactory.get_repository() is ProviderFactory.get_repository()
            repo_cls.assert_called_once()


class TestGetDocumentLoader:
    """Tests for get_document_loader() — no provider dispatch."""

    def test_returns_multi_format_loader(self):
        with patch(
            "src.infrastructure.factories.provider_factory.MultiFormatDocumentLoader"
        ) as loader_cls:
            loader_cls.return_value = "loader"
            assert ProviderFactory.get_document_loader() == "loader"

    def test_singleton(self):
        with patch(
            "src.infrastructure.factories.provider_factory.MultiFormatDocumentLoader"
        ) as loader_cls:
            loader_cls.return_value = MagicMock()
            a = ProviderFactory.get_document_loader()
            b = ProviderFactory.get_document_loader()
            assert a is b
            loader_cls.assert_called_once()


class TestReset:
    """Tests for reset() — clears all caches."""

    def test_reset_clears_all_caches(self):
        with patch(
            "src.infrastructure.factories.provider_factory.get_settings",
            return_value=_settings(llm_provider="openai"),
        ), patch(
            "src.infrastructure.factories.provider_factory.OpenAIEmbeddingsAdapter"
        ) as emb_cls, patch(
            "src.infrastructure.factories.provider_factory.OpenAILLMAdapter"
        ) as llm_cls, patch(
            "src.infrastructure.factories.provider_factory.PGVectorRepository"
        ) as repo_cls, patch(
            "src.infrastructure.factories.provider_factory.MultiFormatDocumentLoader"
        ) as loader_cls:
            for c in (emb_cls, llm_cls, repo_cls, loader_cls):
                c.return_value = MagicMock()

            ProviderFactory.get_embeddings()
            ProviderFactory.get_llm()
            ProviderFactory.get_repository()
            ProviderFactory.get_document_loader()

            ProviderFactory.reset()

            ProviderFactory.get_embeddings()
            ProviderFactory.get_llm()
            ProviderFactory.get_repository()
            ProviderFactory.get_document_loader()

            # Each adapter must have been instantiated exactly twice (pre + post reset).
            assert emb_cls.call_count == 2
            assert llm_cls.call_count == 2
            # repo_cls also called twice (relies on embeddings being recreated).
            assert repo_cls.call_count == 2
            assert loader_cls.call_count == 2
