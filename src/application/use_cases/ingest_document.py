"""
Ingest Document Use Case.
Handles document ingestion with chunking and storage.
"""
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import get_settings
from src.domain.entities.document import Document, DocumentChunk
from src.domain.ports.repository import RepositoryPort
from src.domain.ports.document_loader import DocumentLoaderPort
from src.domain.exceptions import IngestionError, InvalidDocumentError, UnsupportedFormatError


class IngestDocumentUseCase:
    """Use case for ingesting documents."""

    def __init__(self, repository: RepositoryPort, document_loader: DocumentLoaderPort):
        self._repository = repository
        self._document_loader = document_loader
        self._settings = get_settings()
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
        )

    def execute(
        self,
        file_path: str,
        source_name: str | None = None,
        clear_existing: bool = False
    ) -> Document:
        """
        Ingest a document.

        Args:
            file_path: Path to the document file.
            source_name: Optional name for the source (defaults to filename).
            clear_existing: If True, clear existing documents first.

        Returns:
            Document entity with the ingested chunks.

        Raises:
            UnsupportedFormatError: If the file format is not supported.
            IngestionError: If ingestion fails.
            InvalidDocumentError: If the document is invalid.
        """
        try:
            if source_name is None:
                source_name = Path(file_path).name

            pages = self._document_loader.load(file_path, file_name=source_name)

            if not pages:
                raise InvalidDocumentError(f"Document '{source_name}' is empty")

            langchain_chunks = self._text_splitter.split_documents(pages)

            chunks = []
            for lc_chunk in langchain_chunks:
                metadata = dict(lc_chunk.metadata)
                metadata["source_file"] = source_name
                chunks.append(DocumentChunk(
                    content=lc_chunk.page_content,
                    metadata=metadata
                ))

            self._repository.add_documents(chunks, clear_existing=clear_existing)

            return Document(name=source_name, chunks=chunks)

        except (InvalidDocumentError, UnsupportedFormatError):
            raise
        except Exception as e:
            raise IngestionError(f"Failed to ingest '{file_path}': {str(e)}") from e
