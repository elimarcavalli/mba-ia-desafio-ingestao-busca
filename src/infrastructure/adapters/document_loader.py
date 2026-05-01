"""
Multi-format document loader adapter.
Implements DocumentLoaderPort for various file formats.
"""
import json
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    BSHTMLLoader,
    Docx2txtLoader,
)
from langchain_core.documents import Document as LangchainDocument

from src.domain.ports.document_loader import DocumentLoaderPort
from src.domain.exceptions import UnsupportedFormatError, InvalidDocumentError


class MultiFormatDocumentLoader(DocumentLoaderPort):
    """Document loader supporting multiple file formats."""

    _LOADERS = {
        "pdf": lambda path: PyPDFLoader(path).load(),
        "txt": lambda path: TextLoader(path, autodetect_encoding=True).load(),
        "csv": lambda path: CSVLoader(path).load(),
        "html": lambda path: BSHTMLLoader(path).load(),
        "htm": lambda path: BSHTMLLoader(path).load(),
        "md": lambda path: TextLoader(path, autodetect_encoding=True).load(),
        "docx": lambda path: Docx2txtLoader(path).load(),
        "json": None,  # handled by _load_json
    }

    def load(self, file_path: str, file_name: str | None = None) -> list:
        """Load a document from file."""
        ext_source = file_name or file_path
        ext = Path(ext_source).suffix.lstrip(".").lower()

        if not ext or ext not in self._LOADERS:
            supported = ", ".join(sorted(self.supported_extensions()))
            raise UnsupportedFormatError(
                f"Unsupported format '{Path(ext_source).suffix or '(none)'}'. Supported: {supported}"
            )

        if ext == "json":
            return self._load_json(file_path)

        return self._LOADERS[ext](file_path)

    def supported_extensions(self) -> set[str]:
        """Return supported file extensions."""
        return set(self._LOADERS.keys())

    @staticmethod
    def _load_json(file_path: str) -> list:
        """Load a JSON file as a single document."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDocumentError(f"Invalid JSON in '{file_path}': {e}") from e

        if isinstance(data, list):
            text = "\n\n".join(
                item if isinstance(item, str) else json.dumps(item, ensure_ascii=False, indent=2)
                for item in data
            )
        else:
            text = json.dumps(data, ensure_ascii=False, indent=2)

        if not text.strip():
            return []

        return [
            LangchainDocument(
                page_content=text,
                metadata={"source": file_path},
            )
        ]
