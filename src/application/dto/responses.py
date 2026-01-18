"""
Data Transfer Objects for responses.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class IngestResponse:
    """Response from document ingestion."""
    document_name: str
    chunk_count: int
    success: bool
    error_message: str | None = None


@dataclass  
class SearchResponse:
    """Response from document search."""
    query: str
    answer: str
    source_count: int
    success: bool
    error_message: str | None = None
