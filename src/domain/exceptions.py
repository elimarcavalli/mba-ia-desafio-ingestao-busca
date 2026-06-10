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


class UnsupportedFormatError(DomainException):
    """Raised when a document format is not supported."""
    pass


class InvalidCredentialsError(DomainException):
    """Raised when user credentials cannot be verified."""
    pass


class InvalidUsernameError(DomainException):
    """Raised when a username does not match the format policy."""
    pass


class WeakPasswordError(DomainException):
    """Raised when a password does not meet the strength policy."""
    pass
