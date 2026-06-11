"""
Document ingestion entry point.
Ingests the document defined by PDF_PATH in .env (default: document.pdf).

Usage (from project root, after `docker compose up -d`):
    python3 src/ingest.py                           # ingest PDF_PATH from .env (replaces collection)
    python3 src/ingest.py path/to/file.pdf          # ingest a specific file (replaces collection)
    python3 src/ingest.py path/to/file.pdf --append # add a file, keeping previously ingested ones
"""
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def _ensure_venv_python():
    """Re-exec with the project venv interpreter when invoked with system Python."""
    venv_dir = os.path.join(PROJECT_ROOT, "venv")
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    exe = "python.exe" if sys.platform == "win32" else "python"
    venv_python = os.path.join(venv_dir, bin_dir, exe)
    in_project_venv = os.path.realpath(sys.prefix) == os.path.realpath(venv_dir)
    if not in_project_venv and os.path.exists(venv_python):
        os.execv(venv_python, [venv_python, os.path.abspath(__file__), *sys.argv[1:]])

def ingest(file_path: str | None = None, append: bool = False):
    """Ingest a document into the vector store. Returns the Document entity."""
    from src.config.settings import get_settings
    from src.infrastructure.factories.provider_factory import ProviderFactory
    from src.application.use_cases.ingest_document import IngestDocumentUseCase

    if file_path is None:
        file_path = get_settings().pdf_path

    if not os.path.isabs(file_path):
        file_path = os.path.join(PROJECT_ROOT, file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document not found: {file_path}")

    use_case = IngestDocumentUseCase(
        ProviderFactory.get_repository(),
        ProviderFactory.get_document_loader(),
    )
    return use_case.execute(file_path, clear_existing=not append)


def main():
    _ensure_venv_python()

    args = sys.argv[1:]
    append = "--append" in args
    positional = [a for a in args if a != "--append"]
    file_path = positional[0] if positional else None

    print("🔄 Starting ingestion..." + (" (append mode)" if append else ""))
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
        document = ingest(file_path, append=append)
    except ModuleNotFoundError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install dependencies first: run `python3 main.py` (option 1)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        print("💡 Is Docker up (`docker compose up -d`)? Is `.env` configured?")
        sys.exit(1)

    print(f"✅ Ingestion complete! '{document.name}' → {document.chunk_count} chunks stored.")
    print('💬 Now ask away: python3 src/chat.py "your question"')


if __name__ == "__main__":
    main()
