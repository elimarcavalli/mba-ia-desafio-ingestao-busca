"""
Chainlit Web Interface.
Web-based chat interface for document Q&A.

Run with: chainlit run chainlit_app.py --port 8000
"""
import os
import sys
import asyncio
import logging

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

# Suppress noisy asyncio ConnectionResetError on Windows
# This is a known issue with Proactor event loop when WebSocket connections close
if sys.platform == 'win32':
    # Filter out ConnectionResetError from asyncio logs
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

import chainlit as cl
from dotenv import load_dotenv

from src.infrastructure.factories.provider_factory import ProviderFactory
from src.application.use_cases.ingest_document import IngestDocumentUseCase
from src.application.use_cases.search_documents import SearchDocumentsUseCase

load_dotenv()


@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    """
    Resume a previous chat thread.
    Restores the search context from the persisted thread metadata.
    """
    # Get pdf_data from thread metadata
    metadata = thread.get("metadata", {})
    pdf_data = metadata.get("pdf_data", {})
    
    cl.user_session.set("pdf_data", pdf_data)
    
    if pdf_data:
        # Restore search capability using existing documents in vector store
        try:
            repository = ProviderFactory.get_repository()
            llm = ProviderFactory.get_llm()
            search_use_case = SearchDocumentsUseCase(repository, llm)
            cl.user_session.set("search_use_case", search_use_case)
            
            total_chunks = sum(pdf_data.values())
            await cl.Message(
                content=f"♻️ **Welcome back!** Your session has been restored! 🎉\n\n"
                        f"📚 You have **{len(pdf_data)} PDF(s)** ready to chat with ({total_chunks} chunks loaded)\n"
                        f"💬 Feel free to continue asking questions!",
                actions=[
                    cl.Action(name="show_pdfs", payload={}, label="📚 View My PDFs")
                ]
            ).send()
        except Exception as e:
            await cl.Message(content=f"⚠️ Error restoring context: {str(e)}").send()
    else:
        await cl.Message(
            content="👋 **Welcome back!** Your session was restored, but no PDFs are loaded yet.\n\n"
                    "📄 Upload a PDF to start chatting with your documents!",
        ).send()


async def update_thread_metadata():
    """Update thread metadata with current pdf_data.

    This is a best-effort operation - if it fails, the session still works,
    but chat resume may not restore the full context.
    """
    try:
        pdf_data = cl.user_session.get("pdf_data") or {}

        # Get thread_id from session context
        if not hasattr(cl.context, 'session') or not hasattr(cl.context.session, "thread_id"):
            return  # No session context available, skip silently

        thread_id = cl.context.session.thread_id
        if not thread_id:
            return  # No thread_id, skip silently

        # Try to update thread metadata using Chainlit's data layer
        # This may fail if data layer is not fully configured
        try:
            thread = cl.Thread(id=thread_id, metadata={"pdf_data": pdf_data})
            if hasattr(thread, 'update'):
                await thread.update()
        except (AttributeError, TypeError):
            # cl.Thread or update() not available in this Chainlit version
            pass

    except Exception:
        # Silently ignore - thread metadata is optional for core functionality
        pass



async def show_pdf_list():
    """Display list of PDFs with delete buttons."""
    pdf_data = cl.user_session.get("pdf_data") or {}
    
    if not pdf_data:
        await cl.Message(content="📦 **No PDFs loaded yet!** Upload a document to get started. 🚀").send()
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
    """Handle PDF deletion."""
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
        
        # Persist to thread metadata
        await update_thread_metadata()
        
        # Recreate search use case if documents remain
        if pdf_data:
            llm = ProviderFactory.get_llm()
            search_use_case = SearchDocumentsUseCase(repository, llm)
            cl.user_session.set("search_use_case", search_use_case)
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
    """Refresh PDF list."""
    await show_pdf_list()


@cl.action_callback("show_pdfs")
async def handle_show_pdfs(action: cl.Action):
    """Show PDF list from button."""
    await show_pdf_list()


async def process_pdf(pdf_file, clear_first: bool = False) -> tuple[int, str]:
    """Process uploaded PDF file."""
    repository = ProviderFactory.get_repository()
    ingest_use_case = IngestDocumentUseCase(repository)
    
    document = await cl.make_async(ingest_use_case.execute)(
        pdf_file.path, 
        source_name=pdf_file.name,
        clear_existing=clear_first
    )
    
    # Create/update search use case
    llm = ProviderFactory.get_llm()
    search_use_case = SearchDocumentsUseCase(repository, llm)
    cl.user_session.set("search_use_case", search_use_case)
    
    return document.chunk_count, pdf_file.name


@cl.set_starters
async def set_starters():
    """Define Chat Starters for the welcome screen."""
    return [
        cl.Starter(
            label="📄 Upload PDF",
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
    
    # Check for attached PDFs
    if message.elements:
        pdf_files = [el for el in message.elements if el.mime == "application/pdf"]
        
        if pdf_files:
            pdf_data = cl.user_session.get("pdf_data") or {}
            clear_first = len(pdf_data) == 0
            
            for pdf_el in pdf_files:
                msg = cl.Message(content=f"🚀 Processing **{pdf_el.name}**... This will just take a moment!")
                await msg.send()
                
                try:
                    chunk_count, pdf_name = await process_pdf(pdf_el, clear_first)
                    clear_first = False
                    
                    pdf_data[pdf_name] = chunk_count
                    cl.user_session.set("pdf_data", pdf_data)
                    
                    await cl.Message(
                        content=f"✅ **Success!** {pdf_name} is ready ({chunk_count} chunks) 🎉",
                        actions=[
                            cl.Action(name="show_pdfs", payload={}, label="📚 View All Documents"),
                        ]
                    ).send()
                    
                except Exception as e:
                    print(f"Error deleting PDF: {e}")
                    await cl.Message(content=f"❌ **Oops!** Something went wrong: {str(e)}").send()
            
            # Persist all added PDFs to thread metadata
            await update_thread_metadata()
            
            return
    
    # Check for commands
    cmd = message.content.strip().lower()
    
    if cmd in ["/files", "/arquivos", "/pdfs", "/listar"]:
        await show_pdf_list()
        return
    
    # Starter: Upload PDF
    if cmd == "/upload":
        files = await cl.AskFileMessage(
            content="📂 **Select your PDF files:**\n\nYou can choose multiple documents at once!",
            accept=["application/pdf"],
            max_size_mb=50,
            max_files=10,
            timeout=300,
        ).send()
        
        if not files:
            await cl.Message(content="❌ No files selected. Try again when you're ready! 😊").send()
            return
        
        pdf_data = cl.user_session.get("pdf_data") or {}
        clear_first = len(pdf_data) == 0
        
        for pdf_file in files:
            msg = cl.Message(content=f"🚀 Processing **{pdf_file.name}**... Hang tight!")
            await msg.send()
            
            try:
                chunk_count, pdf_name = await process_pdf(pdf_file, clear_first)
                clear_first = False
                
                pdf_data[pdf_name] = chunk_count
                cl.user_session.set("pdf_data", pdf_data)
                
                await cl.Message(
                    content=f"✅ **{pdf_name}** is ready to chat! ({chunk_count} chunks) 🎉",
                    actions=[
                        cl.Action(name="show_pdfs", payload={}, label="📚 View All Documents"),
                    ]
                ).send()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                await cl.Message(content=f"❌ **Oops!** Something went wrong: {str(e)}").send()
        
        # Persist to thread metadata
        await update_thread_metadata()
        
        total_chunks = sum(pdf_data.values())
        await cl.Message(
            content=f"🎉 **All set!** You have **{len(pdf_data)} document{'s' if len(pdf_data) != 1 else ''}** ready ({total_chunks} chunks)\n\n"
                    "💬 Start asking questions about your documents!",
        ).send()
        return
    
    # Starter: Help
    if cmd == "/help":
        await cl.Message(
            content="## 🚀 Welcome to Your Smart Document Assistant!\n\n"
                    "This is a **RAG (Retrieval-Augmented Generation)** system - think of it as your personal "
                    "research assistant that reads your PDFs and answers your questions!\n\n"
                    "## 🎯 How it works:\n\n"
                    "1. **📄 Upload your PDFs** - Use the upload button or simply drag files into the chat\n"
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
    
    # Starter: Examples
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
    search_use_case = cl.user_session.get("search_use_case")
    
    if not search_use_case:
        await cl.Message(
            content="📄 **No documents loaded yet!**\n\n"
                    "Upload a PDF first to start asking questions. Click the 📄 button above or use `/upload`!",
            actions=[
                cl.Action(name="show_pdfs", payload={}, label="📚 View Documents")
            ]
        ).send()
        return
    
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        result = await cl.make_async(search_use_case.execute)(message.content)
        msg.content = result.answer
        await msg.update()
    except Exception as e:
        msg.content = f"❌ **Oops!** Something went wrong: {str(e)}"
        await msg.update()
