"""
CLI Chat interface.
Interactive command-line chat for document Q&A.
"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

from src.infrastructure.factories.provider_factory import ProviderFactory
from src.application.use_cases.ingest_document import IngestDocumentUseCase
from src.application.use_cases.search_documents import SearchDocumentsUseCase


def list_documents(directory: str = ".") -> list[str]:
    """List all supported document files in a directory."""
    supported = ProviderFactory.get_document_loader().supported_extensions()
    docs = []
    for file in os.listdir(directory):
        ext = Path(file).suffix.lstrip(".").lower()
        if ext in supported:
            docs.append(file)
    return sorted(docs)


def select_document() -> str | None:
    """Let user select a document file interactively."""
    docs = list_documents()

    if not docs:
        supported = ProviderFactory.get_document_loader().supported_extensions()
        print("❌ No supported files found in the current directory.")
        print(f"   Supported formats: {', '.join(sorted(supported))}")
        return None

    print("\n📁 Available Documents:")
    for i, doc in enumerate(docs, 1):
        print(f"  {i}. {doc}")

    while True:
        try:
            choice = input(f"\n✨ Select a number (1-{len(docs)}): ").strip()
            if not choice:
                return None
            index = int(choice) - 1
            if 0 <= index < len(docs):
                return docs[index]
            print("⚠️ Invalid number.")
        except ValueError:
            print("⚠️ Please enter a valid number.")
        except KeyboardInterrupt:
            return None


def main():
    """Main CLI entry point."""
    load_dotenv()
    
    print("=" * 50)
    print("🔍 RAG Semantic Search System - CLI")
    print("=" * 50)
    
    # Select document
    doc_file = select_document()
    if not doc_file:
        print("👋 See you later!")
        return

    print(f"\n📄 Selected: {doc_file}")
    print("🔄 Starting ingestion...")

    try:
        # Get dependencies
        repository = ProviderFactory.get_repository()
        llm = ProviderFactory.get_llm()
        document_loader = ProviderFactory.get_document_loader()

        # Ingest document
        ingest_use_case = IngestDocumentUseCase(repository, document_loader)
        document = ingest_use_case.execute(doc_file, clear_existing=True)
        
        print(f"✅ Ingestion complete! {document.chunk_count} chunks created.")
        
        # Create search use case
        search_use_case = SearchDocumentsUseCase(repository, llm)
        
        print("\n" + "=" * 50)
        print("💬 Chat started! Type 'exit' to quit.")
        print("=" * 50 + "\n")
        
        # Chat loop
        while True:
            try:
                question = input("You: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ["sair", "exit", "quit", "q"]:
                    print("👋 See you later!")
                    break
                
                print("🔍 Searching...")
                result = search_use_case.execute(question)
                print(f"\n🧠 DocMind:\n{result.answer}\n")
                
            except KeyboardInterrupt:
                print("\n👋 See you later!")
                break
                
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
