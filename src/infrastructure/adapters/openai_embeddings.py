"""
OpenAI Embeddings adapter.
Implements EmbeddingsPort for OpenAI.
"""
from typing import List

from langchain_openai import OpenAIEmbeddings

from src.config.settings import get_settings
from src.domain.ports.embeddings import EmbeddingsPort


class OpenAIEmbeddingsAdapter(EmbeddingsPort):
    """OpenAI embeddings adapter."""
    
    def __init__(self):
        settings = get_settings()
        self._embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents."""
        return self._embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a query."""
        return self._embeddings.embed_query(text)
    
    def get_langchain_embeddings(self) -> OpenAIEmbeddings:
        """Get LangChain embeddings object."""
        return self._embeddings
