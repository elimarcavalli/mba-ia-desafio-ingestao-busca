"""
Chainlit Web Interface.
Web-based chat interface for document Q&A.

Run with: chainlit run chainlit_app.py --port 8000
"""
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

import chainlit as cl
from dotenv import load_dotenv

from src.infrastructure.factories.provider_factory import ProviderFactory
from src.application.use_cases.ingest_document import IngestDocumentUseCase
from src.application.use_cases.search_documents import SearchDocumentsUseCase

load_dotenv()


async def show_pdf_list():
    """Display list of PDFs with delete buttons."""
    pdf_data = cl.user_session.get("pdf_data") or {}
    
    if not pdf_data:
        await cl.Message(content="📭 Nenhum PDF carregado ainda.").send()
        return
    
    content = "📚 **PDFs no Contexto:**\n\n"
    actions = []
    
    for pdf_name, chunks in pdf_data.items():
        content += f"• **{pdf_name}** ({chunks} chunks)\n"
        actions.append(
            cl.Action(
                name="delete_pdf",
                payload={"pdf_name": pdf_name},
                label=f"❌ Excluir {pdf_name}",
            )
        )
    
    total_chunks = sum(pdf_data.values())
    content += f"\n📊 **Total:** {len(pdf_data)} arquivos, {total_chunks} chunks"
    
    actions.append(
        cl.Action(name="refresh_list", payload={}, label="🔄 Atualizar Lista")
    )
    
    await cl.Message(content=content, actions=actions).send()


@cl.action_callback("delete_pdf")
async def handle_delete_pdf(action: cl.Action):
    """Handle PDF deletion."""
    pdf_name = action.payload.get("pdf_name")
    
    msg = cl.Message(content=f"🗑️ Excluindo **{pdf_name}**...")
    await msg.send()
    
    try:
        repository = ProviderFactory.get_repository()
        deleted = await cl.make_async(repository.delete_by_source)(pdf_name)
        
        pdf_data = cl.user_session.get("pdf_data") or {}
        if pdf_name in pdf_data:
            del pdf_data[pdf_name]
        cl.user_session.set("pdf_data", pdf_data)
        
        # Recreate search use case if documents remain
        if pdf_data:
            llm = ProviderFactory.get_llm()
            search_use_case = SearchDocumentsUseCase(repository, llm)
            cl.user_session.set("search_use_case", search_use_case)
        else:
            cl.user_session.set("search_use_case", None)
        
        await cl.Message(
            content=f"✅ **{pdf_name}** excluído! ({deleted} chunks removidos)"
        ).send()
        
        await show_pdf_list()
        
    except Exception as e:
        await cl.Message(content=f"❌ Erro ao excluir: {str(e)}").send()


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


@cl.on_chat_start
async def start():
    """Initialize chat session."""
    cl.user_session.set("pdf_data", {})
    
    await cl.Message(
        content="# 🔍 Sistema de Busca Semântica\n\n"
                "Envie um arquivo **PDF** para começar.\n\n"
                "📎 Anexe **múltiplos PDFs** para expandir o contexto!",
        actions=[
            cl.Action(name="show_pdfs", payload={}, label="📚 Ver PDFs Carregados")
        ]
    ).send()
    
    files = await cl.AskFileMessage(
        content="📄 **Selecione o primeiro arquivo PDF:**",
        accept=["application/pdf"],
        max_size_mb=50,
        timeout=300,
    ).send()
    
    if not files:
        await cl.Message(content="❌ Nenhum arquivo selecionado.").send()
        return
    
    pdf_file = files[0]
    
    msg = cl.Message(content=f"🔄 Processando **{pdf_file.name}**...")
    await msg.send()
    
    try:
        chunk_count, pdf_name = await process_pdf(pdf_file, clear_first=True)
        
        pdf_data = {pdf_name: chunk_count}
        cl.user_session.set("pdf_data", pdf_data)
        
        await cl.Message(
            content=f"✅ **{pdf_name}** processado! ({chunk_count} chunks)\n\n"
                    "💡 Anexe mais PDFs pelo 📎, arraste ou faça perguntas!",
            actions=[
                cl.Action(name="show_pdfs", payload={}, label="📚 Ver PDFs"),
            ]
        ).send()
        
    except Exception as e:
        await cl.Message(content=f"❌ Erro: {str(e)}").send()


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
                msg = cl.Message(content=f"🔄 Adicionando **{pdf_el.name}**...")
                await msg.send()
                
                try:
                    chunk_count, pdf_name = await process_pdf(pdf_el, clear_first)
                    clear_first = False
                    
                    pdf_data[pdf_name] = chunk_count
                    cl.user_session.set("pdf_data", pdf_data)
                    
                    await cl.Message(
                        content=f"✅ **{pdf_name}** adicionado! ({chunk_count} chunks)",
                        actions=[
                            cl.Action(name="show_pdfs", payload={}, label="📚 Ver Todos PDFs"),
                        ]
                    ).send()
                    
                except Exception as e:
                    await cl.Message(content=f"❌ Erro: {str(e)}").send()
            
            return
    
    # Check for commands
    if message.content.strip().lower() in ["/arquivos", "/pdfs", "/listar"]:
        await show_pdf_list()
        return
    
    # Regular search
    search_use_case = cl.user_session.get("search_use_case")
    
    if not search_use_case:
        await cl.Message(
            content="⚠️ Envie um PDF primeiro.",
            actions=[
                cl.Action(name="show_pdfs", payload={}, label="📚 Ver PDFs")
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
        msg.content = f"❌ Erro: {str(e)}"
        await msg.update()
