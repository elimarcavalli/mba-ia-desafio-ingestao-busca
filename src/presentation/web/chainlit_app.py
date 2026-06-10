"""
Chainlit Web Interface.
Web-based chat interface for document Q&A.

Run with: chainlit run chainlit_app.py --port 8000
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

# Suppress noisy asyncio ConnectionResetError on Windows
# This is a known issue with Proactor event loop when WebSocket connections close
if sys.platform == 'win32':
    class ConnectionResetFilter(logging.Filter):
        def filter(self, record):
            if record.exc_info:
                exc_type = record.exc_info[0]
                if exc_type is ConnectionResetError:
                    return False
            if 'ConnectionResetError' in record.getMessage():
                return False
            return True

    logging.getLogger('asyncio').addFilter(ConnectionResetFilter())

from typing import Optional

import chainlit as cl
from dotenv import load_dotenv

from src.application.use_cases.authenticate_or_register_user import (
    AuthenticateOrRegisterUserUseCase,
)
from src.application.use_cases.ingest_document import IngestDocumentUseCase
from src.application.use_cases.search_documents import SearchDocumentsUseCase
from src.domain.exceptions import DomainException
from src.infrastructure.factories.provider_factory import ProviderFactory

load_dotenv()


@cl.password_auth_callback
async def _auth(identifier: str, password: str) -> Optional[cl.User]:
    """Sign-in or sign-up: unknown identifiers create an account on first login.

    # Returning a cl.User grants access; returning None causes Chainlit to show a login error.
    # Any error here is logged and results in a generic login failure message for the user.
    """
    use_case = AuthenticateOrRegisterUserUseCase(
        ProviderFactory.get_user_repository(),
        ProviderFactory.get_password_hasher(),
    )
    safe_id = (identifier or "").strip()[:64]
    try:
        user = await cl.make_async(use_case.execute)(identifier, password)
    except DomainException as exc:
        print(f"[auth] denied for '{safe_id}': {type(exc).__name__}: {exc}", file=sys.stderr)
        return None
    except Exception as exc:
        # Fail closed on unexpected infrastructure errors.
        print(f"[auth] unexpected error for '{safe_id}': {type(exc).__name__}: {exc}", file=sys.stderr)
        return None

    print(f"[auth] success: {user.identifier}", file=sys.stderr)
    return cl.User(identifier=user.identifier, display_name=user.identifier)


# MIME types for the Chainlit file picker accept list
SUPPORTED_MIMES = [
    "application/pdf",
    "text/plain",
    "text/csv",
    "text/html",
    "application/json",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


def _is_supported_file(element) -> bool:
    """Check if a file element has a supported extension."""
    if not element.name:
        return False
    ext = Path(element.name).suffix.lstrip(".").lower()
    return ext in ProviderFactory.get_document_loader().supported_extensions()


def _create_search_use_case() -> SearchDocumentsUseCase:
    """Create a SearchDocumentsUseCase from factory singletons."""
    return SearchDocumentsUseCase(ProviderFactory.get_repository(), ProviderFactory.get_llm())


@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    """Resume a previous chat thread."""
    # Kept as "pdf_data" for backward compat with persisted sessions
    metadata = thread.get("metadata", {})
    pdf_data = metadata.get("pdf_data", {})

    cl.user_session.set("pdf_data", pdf_data)

    if pdf_data:
        try:
            cl.user_session.set("search_use_case", _create_search_use_case())
            total_chunks = sum(pdf_data.values())
            await cl.Message(
                content=f"♻️ **Welcome back!** Your session has been restored! 🎉\n\n"
                        f"📚 You have **{len(pdf_data)} document(s)** ready to chat with ({total_chunks} chunks loaded)\n"
                        f"💬 Feel free to continue asking questions!",
                actions=[
                    cl.Action(name="show_pdfs", payload={}, label="📚 View My Documents")
                ]
            ).send()
        except Exception as e:
            await cl.Message(content=f"⚠️ Error restoring context: {str(e)}").send()
    else:
        await cl.Message(
            content="👋 **Welcome back!** Your session was restored, but no documents are loaded yet.\n\n"
                    "📄 Upload a document to start chatting!",
        ).send()


async def update_thread_metadata():
    """Update thread metadata with current pdf_data.

    Best-effort — if it fails, the session still works,
    but chat resume may not restore the full context.
    """
    try:
        pdf_data = cl.user_session.get("pdf_data") or {}

        if not hasattr(cl.context, 'session') or not hasattr(cl.context.session, "thread_id"):
            return

        thread_id = cl.context.session.thread_id
        if not thread_id:
            return

        # May fail if data layer is not fully configured or Chainlit version differs
        try:
            thread = cl.Thread(id=thread_id, metadata={"pdf_data": pdf_data})
            await thread.update()
        except (AttributeError, TypeError):
            pass

    except Exception:
        pass



async def show_pdf_list():
    """Display list of documents with delete buttons."""
    pdf_data = cl.user_session.get("pdf_data") or {}

    if not pdf_data:
        await cl.Message(content="📦 **No documents loaded yet!** Upload a file to get started. 🚀").send()
        return

    content = "📚 **Your Document Library:**\n\n"
    actions = []

    for pdf_name, chunks in pdf_data.items():
        content += f"• **{pdf_name}** ({chunks} chunks)\n"
        actions.append(
            cl.Action(
                name="delete_pdf",
                payload={"pdf_name": pdf_name},
                label=f"❌ Delete {pdf_name}",
            )
        )

    total_chunks = sum(pdf_data.values())
    content += f"\n📊 **Total:** {len(pdf_data)} document{'s' if len(pdf_data) != 1 else ''} • {total_chunks} chunks"

    actions.append(
        cl.Action(name="refresh_list", payload={}, label="🔄 Refresh List")
    )

    await cl.Message(content=content, actions=actions).send()


@cl.action_callback("delete_pdf")
async def handle_delete_pdf(action: cl.Action):
    """Handle document deletion."""
    pdf_name = action.payload.get("pdf_name")

    msg = cl.Message(content=f"🗑️ Removing **{pdf_name}** from your library...")
    await msg.send()

    try:
        repository = ProviderFactory.get_repository()
        deleted = await cl.make_async(repository.delete_by_source)(pdf_name)

        pdf_data = cl.user_session.get("pdf_data") or {}
        if pdf_name in pdf_data:
            del pdf_data[pdf_name]
        cl.user_session.set("pdf_data", pdf_data)

        await update_thread_metadata()

        if pdf_data:
            cl.user_session.set("search_use_case", _create_search_use_case())
        else:
            cl.user_session.set("search_use_case", None)

        await cl.Message(
            content=f"✅ **Done!** {pdf_name} has been removed ({deleted} chunks deleted)"
        ).send()

        await show_pdf_list()

    except Exception as e:
        await cl.Message(content=f"❌ **Oops!** Something went wrong: {str(e)}").send()


@cl.action_callback("refresh_list")
async def handle_refresh_list(action: cl.Action):
    """Refresh document list."""
    await show_pdf_list()


@cl.action_callback("show_pdfs")
async def handle_show_pdfs(action: cl.Action):
    """Show document list from button."""
    await show_pdf_list()


async def process_file(file_el, clear_first: bool = False) -> tuple[int, str]:
    """Process an uploaded document file."""
    repository = ProviderFactory.get_repository()
    document_loader = ProviderFactory.get_document_loader()
    ingest_use_case = IngestDocumentUseCase(repository, document_loader)

    document = await cl.make_async(ingest_use_case.execute)(
        file_el.path,
        source_name=file_el.name,
        clear_existing=clear_first
    )

    return document.chunk_count, file_el.name


async def _ingest_files(files) -> None:
    """Shared logic for ingesting a list of uploaded files."""
    pdf_data = cl.user_session.get("pdf_data") or {}
    clear_first = len(pdf_data) == 0

    for file_el in files:
        msg = cl.Message(content=f"🚀 Processing **{file_el.name}**... This will just take a moment!")
        await msg.send()

        try:
            chunk_count, file_name = await process_file(file_el, clear_first)
            clear_first = False

            pdf_data[file_name] = chunk_count
            cl.user_session.set("pdf_data", pdf_data)

            await cl.Message(
                content=f"✅ **{file_name}** is ready! ({chunk_count} chunks) 🎉",
                actions=[
                    cl.Action(name="show_pdfs", payload={}, label="📚 View All Documents"),
                ]
            ).send()

        except Exception as e:
            print(f"Error processing file: {e}")
            await cl.Message(content=f"❌ **Oops!** Something went wrong: {str(e)}").send()

    pdf_data = cl.user_session.get("pdf_data") or {}
    if pdf_data:
        try:
            cl.user_session.set("search_use_case", _create_search_use_case())
        except Exception as e:
            print(f"Error creating search use case: {e}")
    await update_thread_metadata()


async def _answer_question(question: str) -> None:
    """Run a document search for a user question and send the answer."""
    search_use_case = cl.user_session.get("search_use_case")

    if not search_use_case:
        await cl.Message(
            content="📄 **No documents loaded yet!**\n\n"
                    "Upload a document first to start asking questions. Click the 📄 button above or use `/upload`!",
            actions=[
                cl.Action(name="show_pdfs", payload={}, label="📚 View Documents")
            ]
        ).send()
        return

    msg = cl.Message(content="")
    await msg.send()

    try:
        result = await cl.make_async(search_use_case.execute)(question)
        msg.content = result.answer
        await msg.update()
    except Exception as e:
        msg.content = f"❌ **Oops!** Something went wrong: {str(e)}"
        await msg.update()


@cl.set_starters
async def set_starters():
    """Define Chat Starters for the welcome screen."""
    return [
        cl.Starter(
            label="📄 Upload Document",
            message="/upload",
            icon="/public/icons/upload.svg",
        ),
        cl.Starter(
            label="🚀 How does it work?",
            message="/help",
            icon="/public/icons/help.svg",
        ),
        cl.Starter(
            label="💡 See example questions",
            message="/examples",
            icon="/public/icons/example.svg",
        ),
    ]


@cl.on_chat_start
async def start():
    """Initialize chat session silently - Starters handle the welcome."""
    cl.user_session.set("pdf_data", {})


@cl.on_message
async def main(message: cl.Message):
    """Handle user messages and file uploads."""

    # Check for attached documents
    if message.elements:
        supported_files = [el for el in message.elements if _is_supported_file(el)]

        if supported_files:
            await _ingest_files(supported_files)
            question = message.content.strip()
            if question:
                await _answer_question(question)
            return

    # Check for commands
    cmd = message.content.strip().lower()

    if cmd in ["/files", "/arquivos", "/pdfs", "/listar"]:
        await show_pdf_list()
        return

    if cmd == "/upload":
        files = await cl.AskFileMessage(
            content="📂 **Select your files:**\n\nSupported formats: PDF, TXT, CSV, HTML, JSON, Markdown, DOCX.\nYou can choose multiple documents at once!",
            accept=SUPPORTED_MIMES,
            max_size_mb=50,
            max_files=10,
            timeout=300,
        ).send()

        if not files:
            await cl.Message(content="❌ No files selected. Try again when you're ready! 😊").send()
            return

        await _ingest_files(files)

        pdf_data = cl.user_session.get("pdf_data") or {}
        total_chunks = sum(pdf_data.values())
        await cl.Message(
            content=f"🎉 **All set!** You have **{len(pdf_data)} document{'s' if len(pdf_data) != 1 else ''}** ready ({total_chunks} chunks)\n\n"
                    "💬 Start asking questions about your documents!",
        ).send()
        return

    if cmd == "/help":
        await cl.Message(
            content="## 🚀 Welcome to Your Smart Document Assistant!\n\n"
                    "This is a **RAG (Retrieval-Augmented Generation)** system - think of it as your personal "
                    "research assistant that reads your documents and answers your questions!\n\n"
                    "## 📁 Supported Formats:\n\n"
                    "PDF, TXT, CSV, HTML, JSON, Markdown (.md), DOCX\n\n"
                    "## 🎯 How it works:\n\n"
                    "1. **📄 Upload your documents** - Use the upload button or simply drag files into the chat\n"
                    "2. **❓ Ask anything** - Type your questions in natural language\n"
                    "3. **🤖 Get smart answers** - The AI finds relevant info and crafts a precise response\n\n"
                    "## 🛠️ Available Commands:\n\n"
                    "- `/upload` - Add new documents to your library\n"
                    "- `/files` - See all your loaded documents\n"
                    "- `/help` - Show this helpful guide\n"
                    "- `/examples` - Get inspired with example questions\n\n"
                    "💡 **Pro tip:** Answers come exclusively from your uploaded documents - no hallucinations, just facts!",
            actions=[
                cl.Action(name="show_pdfs", payload={}, label="📚 View My Documents"),
            ]
        ).send()
        return

    if cmd == "/examples":
        await cl.Message(
            content="## 💡 Question Ideas to Get Started\n\n"
                    "Not sure what to ask? Here are some examples to inspire you!\n\n"
                    "### 🌐 General Questions:\n"
                    "- *\"What's the main topic of this document?\"*\n"
                    "- *\"Give me a quick summary\"*\n"
                    "- *\"What are the key takeaways?\"*\n"
                    "- *\"List the main points discussed\"*\n\n"
                    "### 🎯 Specific Questions:\n"
                    "- *\"What does the document say about [your topic]?\"*\n"
                    "- *\"What are the conclusions regarding [subject]?\"*\n"
                    "- *\"Explain the concept of [term] from the text\"*\n"
                    "- *\"Find all mentions of [keyword]\"*\n\n"
                    "🎓 **Remember:** The more specific your question, the better the answer! Feel free to ask follow-up questions too.",
        ).send()
        return

    # Regular search
    await _answer_question(message.content)
