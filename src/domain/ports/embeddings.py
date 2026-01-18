"""
Embeddings port (interface).
Defines the contract for embedding providers.
"""
from abc import ABC, abstractmethod
from typing import List


class EmbeddingsPort(ABC):
    """Abstract interface for embeddings providers."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of embedding vectors.
        """
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            text: Query text to embed.
            
        Returns:
            Embedding vector.
        """
        pass
    
    @abstractmethod
    def get_langchain_embeddings(self):
        """
        Get the underlying LangChain embeddings object.
        Required for compatibility with PGVector.
        
        Returns:
            LangChain Embeddings instance.
        """
        pass
