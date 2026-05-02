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


class TestLoadHtml:
    """Tests for loading HTML files."""

    def test_load_html(self, loader, tmp_path):
        f = tmp_path / "page.html"
        f.write_text(
            "<html><body><h1>Title</h1><p>Body content here.</p></body></html>",
            encoding="utf-8",
        )
        docs = loader.load(str(f))
        assert len(docs) >= 1
        combined = " ".join(d.page_content for d in docs)
        assert "Body content here." in combined

    def test_htm_extension_also_supported(self, loader, tmp_path):
        f = tmp_path / "page.htm"
        f.write_text("<html><body>X content Y</body></html>", encoding="utf-8")
        docs = loader.load(str(f))
        combined = " ".join(d.page_content for d in docs)
        assert "X content Y" in combined


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestLoadDocx:
    """Tests for loading DOCX files using a static fixture."""

    def test_load_docx(self, loader):
        f = FIXTURES_DIR / "sample.docx"
        docs = loader.load(str(f))
        assert len(docs) >= 1
        combined = " ".join(d.page_content for d in docs)
        assert "Hello DOCX content." in combined


class TestFileNameHint:
    """Regression tests for the .md upload bug — extension comes from file_name."""

    def test_file_name_overrides_path_extension(self, loader, tmp_path):
        """Chainlit uploads land in /tmp/<uuid> with no extension; file_name carries
        the real format."""
        f = tmp_path / "no_extension_blob"
        f.write_text("# Title\n\nMarkdown body here.", encoding="utf-8")

        docs = loader.load(str(f), file_name="readme.md")

        assert len(docs) >= 1
        assert "Markdown body here." in docs[0].page_content

    def test_file_name_none_falls_back_to_path(self, loader, tmp_txt_file):
        """When file_name is None, extension is read from file_path (CLI path)."""
        docs = loader.load(str(tmp_txt_file), file_name=None)
        assert len(docs) >= 1

    def test_file_name_unsupported_raises_with_correct_extension_in_message(
        self, loader, tmp_path
    ):
        """Error message must reflect the file_name's extension, not the temp path."""
        f = tmp_path / "blob"
        f.write_text("data", encoding="utf-8")
        with pytest.raises(UnsupportedFormatError, match=r"\.xyz"):
            loader.load(str(f), file_name="upload.xyz")

    def test_file_name_with_uppercase_extension(self, loader, tmp_path):
        """Extension detection must be case-insensitive."""
        f = tmp_path / "blob"
        f.write_text("# Title\n", encoding="utf-8")
        docs = loader.load(str(f), file_name="README.MD")
        assert len(docs) >= 1


class TestJsonExtraEdgeCases:
    """Additional JSON edge cases."""

    def test_empty_object_returns_one_doc_with_empty_braces(self, loader, tmp_path):
        f = tmp_path / "empty_obj.json"
        f.write_text("{}", encoding="utf-8")
        docs = loader.load(str(f))
        # `{}` serialized has content, so we get exactly one doc.
        assert len(docs) == 1
        assert "{}" in docs[0].page_content

    def test_json_metadata_includes_source(self, loader, tmp_json_file):
        docs = loader.load(str(tmp_json_file))
        assert docs[0].metadata.get("source") == str(tmp_json_file)

    def test_json_unicode_preserved(self, loader, tmp_path):
        f = tmp_path / "u.json"
        f.write_text(
            json.dumps({"k": "olá mundo — açaí"}, ensure_ascii=False),
            encoding="utf-8",
        )
        docs = loader.load(str(f))
        assert "olá mundo" in docs[0].page_content
        assert "açaí" in docs[0].page_content
