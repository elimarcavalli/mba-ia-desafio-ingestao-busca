"""
Domain exceptions.
Custom exceptions for the domain layer.
"""


class DomainException(Exception):
    """Base exception for domain errors."""
    pass


class DocumentNotFoundError(DomainException):
    """Raised when a document is not found."""
    pass


class IngestionError(DomainException):
    """Raised when document ingestion fails."""
    pass


class SearchError(DomainException):
    """Raised when search fails."""
    pass


class ProviderNotConfiguredError(DomainException):
    """Raised when a required provider is not configured."""
    pass


class InvalidDocumentError(DomainException):
    """Raised when a document is invalid or corrupted."""
    pass
