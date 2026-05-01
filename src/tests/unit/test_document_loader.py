"""
Unit tests for MultiFormatDocumentLoader adapter.
"""
import json
import pytest
from pathlib import Path

from src.infrastructure.adapters.document_loader import MultiFormatDocumentLoader
from src.domain.exceptions import UnsupportedFormatError, InvalidDocumentError


@pytest.fixture
def loader():
    return MultiFormatDocumentLoader()


@pytest.fixture
def tmp_txt_file(tmp_path) -> Path:
    f = tmp_path / "sample.txt"
    f.write_text("Hello world.\nSecond line.", encoding="utf-8")
    return f


@pytest.fixture
def tmp_csv_file(tmp_path) -> Path:
    f = tmp_path / "sample.csv"
    f.write_text("name,age\nAlice,30\nBob,25", encoding="utf-8")
    return f


@pytest.fixture
def tmp_json_file(tmp_path) -> Path:
    f = tmp_path / "sample.json"
    f.write_text(json.dumps({"key": "value", "nested": {"a": 1}}), encoding="utf-8")
    return f


@pytest.fixture
def tmp_json_list_file(tmp_path) -> Path:
    f = tmp_path / "list.json"
    f.write_text(json.dumps(["item1", "item2", {"k": "v"}]), encoding="utf-8")
    return f


@pytest.fixture
def tmp_md_file(tmp_path) -> Path:
    f = tmp_path / "readme.md"
    f.write_text("# Title\n\nSome markdown content.", encoding="utf-8")
    return f


class TestSupportedExtensions:
    """Tests for supported_extensions()."""

    def test_returns_all_formats(self, loader):
        exts = loader.supported_extensions()
        expected = {"pdf", "txt", "csv", "html", "htm", "json", "md", "docx"}
        assert exts == expected

    def test_returns_set(self, loader):
        assert isinstance(loader.supported_extensions(), set)


class TestLoadTxt:
    """Tests for loading TXT files."""

    def test_load_txt(self, loader, tmp_txt_file):
        docs = loader.load(str(tmp_txt_file))
        assert len(docs) >= 1
        assert "Hello world." in docs[0].page_content


class TestLoadCsv:
    """Tests for loading CSV files."""

    def test_load_csv(self, loader, tmp_csv_file):
        docs = loader.load(str(tmp_csv_file))
        assert len(docs) >= 1
        # CSVLoader creates one document per row
        combined = " ".join(d.page_content for d in docs)
        assert "Alice" in combined


class TestLoadJson:
    """Tests for loading JSON files."""

    def test_load_json_object(self, loader, tmp_json_file):
        docs = loader.load(str(tmp_json_file))
        assert len(docs) == 1
        assert "key" in docs[0].page_content
        assert "value" in docs[0].page_content

    def test_load_json_list(self, loader, tmp_json_list_file):
        docs = loader.load(str(tmp_json_list_file))
        assert len(docs) == 1
        assert "item1" in docs[0].page_content


class TestLoadMarkdown:
    """Tests for loading Markdown files."""

    def test_load_md(self, loader, tmp_md_file):
        docs = loader.load(str(tmp_md_file))
        assert len(docs) >= 1
        assert "Title" in docs[0].page_content


class TestLoadJsonEdgeCases:
    """Tests for JSON edge cases."""

    def test_invalid_json_raises_invalid_document_error(self, loader, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not valid json {{{", encoding="utf-8")
        with pytest.raises(InvalidDocumentError, match="Invalid JSON"):
            loader.load(str(f))

    def test_empty_json_array_returns_empty_list(self, loader, tmp_path):
        f = tmp_path / "empty_array.json"
        f.write_text("[]", encoding="utf-8")
        docs = loader.load(str(f))
        assert docs == []


class TestUnsupportedFormat:
    """Tests for unsupported file formats."""

    def test_raises_for_unknown_extension(self, loader, tmp_path):
        f = tmp_path / "file.xyz"
        f.write_text("data")
        with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
            loader.load(str(f))

    def test_raises_for_no_extension(self, loader, tmp_path):
        f = tmp_path / "Makefile"
        f.write_text("all: build")
        with pytest.raises(UnsupportedFormatError, match="none"):
            loader.load(str(f))
