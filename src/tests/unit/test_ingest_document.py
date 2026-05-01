"""
Unit tests for IngestDocumentUseCase.
"""
import pytest

from src.application.use_cases.ingest_document import IngestDocumentUseCase
from src.domain.exceptions import UnsupportedFormatError, InvalidDocumentError, IngestionError


class TestIngestDocumentUseCase:
    """Tests for IngestDocumentUseCase."""

    def test_execute_with_mock_loader(self, mock_repository, mock_document_loader):
        """Test successful ingestion through the use case."""
        use_case = IngestDocumentUseCase(mock_repository, mock_document_loader)

        result = use_case.execute("/path/to/test.txt", source_name="test.txt")

        assert result.name == "test.txt"
        assert result.chunk_count >= 1
        mock_document_loader.load.assert_called_once_with("/path/to/test.txt", file_name="test.txt")
        mock_repository.add_documents.assert_called_once()

    def test_execute_infers_source_name(self, mock_repository, mock_document_loader):
        """Test that source_name defaults to the filename."""
        use_case = IngestDocumentUseCase(mock_repository, mock_document_loader)

        result = use_case.execute("/some/path/report.txt")

        assert result.name == "report.txt"

    def test_unsupported_format_raises(self, mock_repository, mock_document_loader):
        """Test that UnsupportedFormatError from loader propagates."""
        mock_document_loader.load.side_effect = UnsupportedFormatError("Unsupported format '.xyz'")
        use_case = IngestDocumentUseCase(mock_repository, mock_document_loader)

        with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
            use_case.execute("/path/to/file.xyz")

    def test_empty_document_raises(self, mock_repository, mock_document_loader):
        """Test that empty document raises InvalidDocumentError."""
        mock_document_loader.load.return_value = []
        use_case = IngestDocumentUseCase(mock_repository, mock_document_loader)

        with pytest.raises(InvalidDocumentError, match="is empty"):
            use_case.execute("/path/to/empty.txt")

    def test_clear_existing_passed_to_repository(self, mock_repository, mock_document_loader):
        """Test that clear_existing flag is forwarded to repository."""
        use_case = IngestDocumentUseCase(mock_repository, mock_document_loader)

        use_case.execute("/path/to/test.txt", clear_existing=True)

        _, kwargs = mock_repository.add_documents.call_args
        assert kwargs["clear_existing"] is True

    def test_loader_exception_wrapped_as_ingestion_error(self, mock_repository, mock_document_loader):
        """Test that loader exceptions are wrapped as IngestionError."""
        mock_document_loader.load.side_effect = RuntimeError("Disk error")
        use_case = IngestDocumentUseCase(mock_repository, mock_document_loader)

        with pytest.raises(IngestionError, match="Failed to ingest"):
            use_case.execute("/path/to/test.txt")
