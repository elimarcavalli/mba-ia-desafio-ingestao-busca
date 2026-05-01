"""
Document loader port (interface).
Defines the contract for loading documents from various file formats.
"""
from abc import ABC, abstractmethod


class DocumentLoaderPort(ABC):
    """Abstract interface for document loaders."""

    @abstractmethod
    def load(self, file_path: str, file_name: str | None = None) -> list:
        """
        Load a document from file and return its contents.

        Args:
            file_path: Path to the document file on disk.
            file_name: Original filename used to detect format. Falls back to
                file_path when omitted. Required when file_path is a temp path
                without a meaningful extension (e.g. Chainlit uploads).

        Returns:
            List of loaded document objects.
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """
        Return the set of supported file extensions.

        Returns:
            Set of extensions without dots (e.g. {"pdf", "txt", "csv"}).
        """
        pass
