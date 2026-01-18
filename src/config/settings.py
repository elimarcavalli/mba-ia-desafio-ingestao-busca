"""
Configuration module using Pydantic BaseSettings.
Centralizes all environment variable configuration.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # LLM Provider
    llm_provider: Literal["openai", "google"] = "openai"
    
    # Database
    database_url: str
    pg_vector_collection_name: str = "document_chunks"
    
    # OpenAI
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    
    # Google
    google_api_key: str | None = None
    google_embedding_model: str = "models/embedding-001"
    google_chat_model: str = "gemini-2.5-flash-lite"
    
    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 150
    retriever_k: int = 10
    llm_timeout: int = 60
    
    @property
    def sqlalchemy_database_url(self) -> str:
        """
        Get database URL formatted for SQLAlchemy/LangChain (psycopgv3).
        Converts 'postgresql://' to 'postgresql+psycopg://' if needed.
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
