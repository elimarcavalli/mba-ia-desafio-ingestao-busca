"""
Domain entities module.
Contains core business objects.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with its content and metadata."""
    
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def source_file(self) -> str | None:
        """Get the source file name from metadata."""
        return self.metadata.get("source_file")
    
    @property
    def page_number(self) -> int | None:
        """Get the page number from metadata."""
        return self.metadata.get("page")


@dataclass
class Document:
    """Represents a document with its chunks."""
    
    name: str
    chunks: list[DocumentChunk] = field(default_factory=list)
    
    @property
    def chunk_count(self) -> int:
        """Get the number of chunks in this document."""
        return len(self.chunks)


@dataclass
class SearchResult:
    """Represents a search result from the RAG system."""
    
    query: str
    answer: str
    sources: list[DocumentChunk] = field(default_factory=list)
