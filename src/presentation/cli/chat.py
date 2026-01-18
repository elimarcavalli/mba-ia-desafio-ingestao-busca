"""
CLI Chat interface.
Interactive command-line chat for document Q&A.
"""
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

from src.infrastructure.factories.provider_factory import ProviderFactory
from src.application.use_cases.ingest_document import IngestDocumentUseCase
from src.application.use_cases.search_documents import SearchDocumentsUseCase


def list_pdfs(directory: str = ".") -> list[str]:
    """List all PDF files in a directory."""
    pdfs = []
    for file in os.listdir(directory):
        if file.lower().endswith(".pdf"):
            pdfs.append(file)
    return sorted(pdfs)


def select_pdf() -> str | None:
    """Let user select a PDF file interactively."""
    pdfs = list_pdfs()
    
    if not pdfs:
        print("❌ Nenhum arquivo PDF encontrado no diretório atual.")
        return None
    
    print("\n📁 PDFs disponíveis:")
    for i, pdf in enumerate(pdfs, 1):
        print(f"  {i}. {pdf}")
    
    while True:
        try:
            choice = input(f"\nSelecione o número (1-{len(pdfs)}): ").strip()
            if not choice:
                return None
            index = int(choice) - 1
            if 0 <= index < len(pdfs):
                return pdfs[index]
            print("⚠️ Número inválido.")
        except ValueError:
            print("⚠️ Digite um número válido.")
        except KeyboardInterrupt:
            return None


def main():
    """Main CLI entry point."""
    load_dotenv()
    
    print("=" * 50)
    print("🔍 Sistema de Busca Semântica - CLI")
    print("=" * 50)
    
    # Select PDF
    pdf_file = select_pdf()
    if not pdf_file:
        print("👋 Até logo!")
        return
    
    print(f"\n📄 PDF selecionado: {pdf_file}")
    print("🔄 Iniciando ingestão...")
    
    try:
        # Get dependencies
        repository = ProviderFactory.get_repository()
        llm = ProviderFactory.get_llm()
        
        # Ingest document
        ingest_use_case = IngestDocumentUseCase(repository)
        document = ingest_use_case.execute(pdf_file, clear_existing=True)
        
        print(f"✅ Ingestão concluída! {document.chunk_count} chunks criados.")
        
        # Create search use case
        search_use_case = SearchDocumentsUseCase(repository, llm)
        
        print("\n" + "=" * 50)
        print("💬 Chat iniciado! Digite 'sair' para encerrar.")
        print("=" * 50 + "\n")
        
        # Chat loop
        while True:
            try:
                question = input("Você: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ["sair", "exit", "quit", "q"]:
                    print("👋 Até logo!")
                    break
                
                print("🔍 Buscando...")
                result = search_use_case.execute(question)
                print(f"\n🤖 Assistente:\n{result.answer}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
