"""
Unit tests for Settings (config layer).
"""
import pytest

from src.config.settings import Settings, get_settings


class TestSqlAlchemyDatabaseUrl:
    """Tests for the postgresql:// → postgresql+psycopg:// conversion."""

    def test_converts_plain_postgresql_url(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pwd@host:5432/db")
        s = Settings()
        assert s.sqlalchemy_database_url == "postgresql+psycopg://user:pwd@host:5432/db"

    def test_keeps_postgresql_psycopg_url_unchanged(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/db")
        s = Settings()
        assert s.sqlalchemy_database_url == "postgresql+psycopg://u:p@h:5432/db"

    def test_only_replaces_first_occurrence(self, monkeypatch):
        # Defensive: even if "postgresql://" appears in the password (unrealistic but
        # the implementation uses count=1).
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql://user:postgresql://x@host/db"
        )
        s = Settings()
        # First occurrence replaced, the (artificial) second left intact.
        assert s.sqlalchemy_database_url.startswith("postgresql+psycopg://user:")

    def test_non_postgresql_url_passthrough(self, monkeypatch):
        # If a future user passes a different URL, do not mangle it.
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./local.db")
        s = Settings()
        assert s.sqlalchemy_database_url == "sqlite:///./local.db"


class TestDefaults:
    """Tests for default values."""

    def test_rag_defaults(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@h/d")
        s = Settings()
        assert s.chunk_size == 1000
        assert s.chunk_overlap == 150
        assert s.retriever_k == 10
        assert s.llm_timeout == 60

    def test_provider_defaults(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@h/d")
        s = Settings()
        assert s.llm_provider == "openai"
        assert s.openai_embedding_model == "text-embedding-3-small"
        assert s.openai_chat_model == "gpt-4o-mini"
        assert s.google_embedding_model == "models/embedding-001"
        assert s.google_chat_model == "gemini-2.5-flash-lite"

    def test_collection_name_default(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@h/d")
        s = Settings()
        assert s.pg_vector_collection_name == "document_chunks"

    def test_invalid_provider_rejected(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@h/d")
        monkeypatch.setenv("LLM_PROVIDER", "cohere")
        with pytest.raises(Exception):  # pydantic ValidationError
            Settings()


class TestGetSettingsCached:
    """Tests for the lru_cache on get_settings."""

    def test_returns_same_instance(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@h/d")
        get_settings.cache_clear()
        a = get_settings()
        b = get_settings()
        assert a is b
        get_settings.cache_clear()
