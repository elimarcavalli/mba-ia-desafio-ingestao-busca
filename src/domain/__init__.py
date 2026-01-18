"""Domain layer - contains entities, ports and exceptions."""
from src.domain.entities import Document, DocumentChunk, SearchResult
from src.domain.ports import EmbeddingsPort, LLMPort, RepositoryPort
from src.domain.exceptions import (
    DomainException,
    DocumentNotFoundError,
    IngestionError,
    SearchError,
    ProviderNotConfiguredError,
    InvalidDocumentError,
)

__all__ = [
    # Entities
    "Document",
    "DocumentChunk", 
    "SearchResult",
    # Ports
    "EmbeddingsPort",
    "LLMPort",
    "RepositoryPort",
    # Exceptions
    "DomainException",
    "DocumentNotFoundError",
    "IngestionError",
    "SearchError",
    "ProviderNotConfiguredError",
    "InvalidDocumentError",
]
