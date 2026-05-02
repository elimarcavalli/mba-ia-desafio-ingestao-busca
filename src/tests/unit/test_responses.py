"""
Unit tests for application DTOs.
"""
from src.application.dto.responses import IngestResponse, SearchResponse


class TestIngestResponse:
    def test_minimal_fields(self):
        r = IngestResponse(document_name="x.pdf", chunk_count=5, success=True)
        assert r.document_name == "x.pdf"
        assert r.chunk_count == 5
        assert r.success is True
        assert r.error_message is None

    def test_with_error(self):
        r = IngestResponse(
            document_name="x.pdf",
            chunk_count=0,
            success=False,
            error_message="boom",
        )
        assert r.success is False
        assert r.error_message == "boom"


class TestSearchResponse:
    def test_minimal_fields(self):
        r = SearchResponse(query="q", answer="a", source_count=3, success=True)
        assert r.query == "q"
        assert r.answer == "a"
        assert r.source_count == 3
        assert r.success is True
        assert r.error_message is None

    def test_with_error(self):
        r = SearchResponse(
            query="q",
            answer="",
            source_count=0,
            success=False,
            error_message="LLM down",
        )
        assert r.success is False
        assert r.error_message == "LLM down"
