"""
Ingest Document Use Case.
Handles PDF ingestion with chunking and storage.
"""
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import get_settings
from src.domain.entities.document import Document, DocumentChunk
from src.domain.ports.repository import RepositoryPort
from src.domain.exceptions import IngestionError, InvalidDocumentError


class IngestDocumentUseCase:
    """Use case for ingesting PDF documents."""
    
    def __init__(self, repository: RepositoryPort):
        self._repository = repository
        self._settings = get_settings()
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
        )
    
    def execute(
        self, 
        pdf_path: str, 
        source_name: str | None = None,
        clear_existing: bool = False
    ) -> Document:
        """
        Ingest a PDF document.
        
        Args:
            pdf_path: Path to the PDF file.
            source_name: Optional name for the source (defaults to filename).
            clear_existing: If True, clear existing documents first.
            
        Returns:
            Document entity with the ingested chunks.
            
        Raises:
            IngestionError: If ingestion fails.
            InvalidDocumentError: If the PDF is invalid.
        """
        try:
            # Determine source name
            if source_name is None:
                source_name = pdf_path.split("/")[-1]
            
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            if not pages:
                raise InvalidDocumentError(f"PDF '{source_name}' is empty")
            
            # Split into chunks
            langchain_chunks = self._text_splitter.split_documents(pages)
            
            # Convert to domain entities
            chunks = []
            for lc_chunk in langchain_chunks:
                metadata = dict(lc_chunk.metadata)
                metadata["source_file"] = source_name
                chunks.append(DocumentChunk(
                    content=lc_chunk.page_content,
                    metadata=metadata
                ))
            
            # Store in repository
            self._repository.add_documents(chunks, clear_existing=clear_existing)
            
            return Document(name=source_name, chunks=chunks)
            
        except InvalidDocumentError:
            raise
        except Exception as e:
            raise IngestionError(f"Failed to ingest '{pdf_path}': {str(e)}") from e
