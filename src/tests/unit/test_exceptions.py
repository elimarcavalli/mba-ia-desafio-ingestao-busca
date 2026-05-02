"""
Unit tests for domain exception hierarchy.
"""
import pytest

from src.domain.exceptions import (
    DocumentNotFoundError,
    DomainException,
    IngestionError,
    InvalidDocumentError,
    ProviderNotConfiguredError,
    SearchError,
    UnsupportedFormatError,
)


CONCRETE_EXCEPTIONS = [
    DocumentNotFoundError,
    IngestionError,
    SearchError,
    ProviderNotConfiguredError,
    InvalidDocumentError,
    UnsupportedFormatError,
]


class TestHierarchy:
    """Every concrete exception must descend from DomainException."""

    @pytest.mark.parametrize("exc_cls", CONCRETE_EXCEPTIONS)
    def test_inherits_from_domain_exception(self, exc_cls):
        assert issubclass(exc_cls, DomainException)

    def test_domain_exception_is_exception(self):
        assert issubclass(DomainException, Exception)

    @pytest.mark.parametrize("exc_cls", CONCRETE_EXCEPTIONS)
    def test_can_be_raised_and_caught_as_domain_exception(self, exc_cls):
        with pytest.raises(DomainException):
            raise exc_cls("msg")

    @pytest.mark.parametrize("exc_cls", CONCRETE_EXCEPTIONS)
    def test_message_preserved(self, exc_cls):
        try:
            raise exc_cls("custom message")
        except DomainException as e:
            assert "custom message" in str(e)
