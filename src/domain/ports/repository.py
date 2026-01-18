"""
Repository port (interface).
Defines the contract for document storage.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.document import DocumentChunk


class RepositoryPort(ABC):
    """Abstract interface for document repository."""
    
    @abstractmethod
    def add_documents(
        self, 
        chunks: List[DocumentChunk], 
        clear_existing: bool = False
    ) -> int:
        """
        Add document chunks to the repository.
        
        Args:
            chunks: List of document chunks to add.
            clear_existing: If True, clear existing documents first.
            
        Returns:
            Number of chunks added.
        """
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 10) -> List[DocumentChunk]:
        """
        Search for similar documents.
        
        Args:
            query: Search query.
            k: Number of results to return.
            
        Returns:
            List of matching document chunks.
        """
        pass
    
    @abstractmethod
    def delete_by_source(self, source_file: str) -> int:
        """
        Delete all chunks from a specific source file.
        
        Args:
            source_file: Name of the source file.
            
        Returns:
            Number of chunks deleted.
        """
        pass
    
    @abstractmethod
    def get_retriever(self, k: int = 10):
        """
        Get a LangChain retriever for the repository.
        
        Args:
            k: Number of results to return.
            
        Returns:
            LangChain Retriever instance.
        """
        pass
