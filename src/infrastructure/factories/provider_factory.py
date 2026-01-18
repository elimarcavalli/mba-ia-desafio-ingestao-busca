"""
Provider factory.
Creates instances of embeddings, LLM, and repository based on configuration.
"""
from src.config.settings import get_settings
from src.domain.ports.embeddings import EmbeddingsPort
from src.domain.ports.llm import LLMPort
from src.domain.ports.repository import RepositoryPort
from src.domain.exceptions import ProviderNotConfiguredError

from src.infrastructure.adapters.openai_embeddings import OpenAIEmbeddingsAdapter
from src.infrastructure.adapters.google_embeddings import GoogleEmbeddingsAdapter
from src.infrastructure.adapters.openai_llm import OpenAILLMAdapter
from src.infrastructure.adapters.google_llm import GoogleLLMAdapter
from src.infrastructure.adapters.pgvector_repository import PGVectorRepository


class ProviderFactory:
    """Factory for creating provider instances."""
    
    _embeddings: EmbeddingsPort | None = None
    _llm: LLMPort | None = None
    _repository: RepositoryPort | None = None
    
    @classmethod
    def get_embeddings(cls) -> EmbeddingsPort:
        """Get embeddings provider based on configuration."""
        if cls._embeddings is not None:
            return cls._embeddings
            
        settings = get_settings()
        
        if settings.llm_provider == "openai":
            if not settings.openai_api_key:
                raise ProviderNotConfiguredError("OpenAI API key not configured")
            cls._embeddings = OpenAIEmbeddingsAdapter()
        elif settings.llm_provider == "google":
            if not settings.google_api_key:
                raise ProviderNotConfiguredError("Google API key not configured")
            cls._embeddings = GoogleEmbeddingsAdapter()
        else:
            raise ProviderNotConfiguredError(f"Unknown provider: {settings.llm_provider}")
        
        return cls._embeddings
    
    @classmethod
    def get_llm(cls) -> LLMPort:
        """Get LLM provider based on configuration."""
        if cls._llm is not None:
            return cls._llm
            
        settings = get_settings()
        
        if settings.llm_provider == "openai":
            if not settings.openai_api_key:
                raise ProviderNotConfiguredError("OpenAI API key not configured")
            cls._llm = OpenAILLMAdapter()
        elif settings.llm_provider == "google":
            if not settings.google_api_key:
                raise ProviderNotConfiguredError("Google API key not configured")
            cls._llm = GoogleLLMAdapter()
        else:
            raise ProviderNotConfiguredError(f"Unknown provider: {settings.llm_provider}")
        
        return cls._llm
    
    @classmethod
    def get_repository(cls) -> RepositoryPort:
        """Get repository instance."""
        if cls._repository is not None:
            return cls._repository
            
        embeddings = cls.get_embeddings()
        cls._repository = PGVectorRepository(embeddings)
        
        return cls._repository
    
    @classmethod
    def reset(cls) -> None:
        """Reset all cached instances. Useful for testing."""
        cls._embeddings = None
        cls._llm = None
        cls._repository = None
