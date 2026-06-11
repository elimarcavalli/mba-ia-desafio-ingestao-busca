"""
Chat entry point.
Asks questions against documents already ingested by `src/ingest.py`.

Usage (from project root, after ingesting):
    python3 src/chat.py                       # interactive chat
    python3 src/chat.py "Your question here"  # one-shot: answer and exit
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

def build_search_use_case():
    """Build the search use case with dependencies from the factory."""
    from src.infrastructure.factories.provider_factory import ProviderFactory
    from src.application.use_cases.search_documents import SearchDocumentsUseCase

    return SearchDocumentsUseCase(
        ProviderFactory.get_repository(),
        ProviderFactory.get_llm(),
    )


def ask(search_use_case, question: str) -> str:
    """Run a single question through the RAG chain and return the answer."""
    return search_use_case.execute(question).answer


def chat_loop(search_use_case):
    """Interactive chat loop. Type 'exit' to quit."""
    print("💬 Chat started! Type 'exit' to quit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 See you later!")
            break

        if not question:
            continue
        if question.lower() in ("sair", "exit", "quit", "q"):
            print("👋 See you later!")
            break

        print("🔍 Searching...")
        print(f"\n🤖 Assistant:\n{ask(search_use_case, question)}\n")


def main():
    _ensure_venv_python()

    question = " ".join(sys.argv[1:]).strip()

    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

        search_use_case = build_search_use_case()

        if question:
            print(f"🔍 Question: {question}")
            print(f"\n🤖 Assistant:\n{ask(search_use_case, question)}")
        else:
            chat_loop(search_use_case)

    except ModuleNotFoundError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install dependencies first: run `python3 main.py` (option 1)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Did you run `python3 src/ingest.py` first? Is Docker up (`docker compose up -d`)?")
        sys.exit(1)


if __name__ == "__main__":
    main()
