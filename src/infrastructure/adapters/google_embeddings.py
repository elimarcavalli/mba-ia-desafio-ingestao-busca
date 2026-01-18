"""
Google Embeddings adapter.
Implements EmbeddingsPort for Google Generative AI.
"""
from typing import List

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.config.settings import get_settings
from src.domain.ports.embeddings import EmbeddingsPort


class GoogleEmbeddingsAdapter(EmbeddingsPort):
    """Google Generative AI embeddings adapter."""
    
    def __init__(self):
        settings = get_settings()
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.google_embedding_model,
            google_api_key=settings.google_api_key,
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents."""
        return self._embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a query."""
        return self._embeddings.embed_query(text)
    
    def get_langchain_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Get LangChain embeddings object."""
        return self._embeddings
