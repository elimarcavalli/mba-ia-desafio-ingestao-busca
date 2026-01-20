"""
Search Documents Use Case.
Handles RAG-based semantic search.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.config.settings import get_settings
from src.domain.entities.document import SearchResult
from src.domain.ports.repository import RepositoryPort
from src.domain.ports.llm import LLMPort
from src.domain.exceptions import SearchError


# PROMPT OTIMIZADO: Estrutura XML + Persona + Regras Estritas
PROMPT_TEMPLATE = """
Você é um Assistente de IA Especialista em Busca Semântica corporativa. Sua função é responder perguntas baseando-se estritamente nos documentos recuperados.

<instrucoes_principais>
1.  **Fonte da Verdade:** Use SOMENTE as informações fornecidas dentro das tags <contexto>. Ignore qualquer conhecimento prévio que você tenha sobre o mundo que não esteja no texto.
2.  **Integridade:** Se a resposta não estiver explícita ou não puder ser deduzida com alta confiança a partir do <contexto>, você DEVE responder: "Não encontrei informações suficientes nos documentos para responder a essa pergunta."
3.  **Objetividade:** Seja direto, profissional e conciso. Evite preâmbulos como "Com base no texto...". Vá direto ao ponto.
4.  **Citação Implícita:** Se houver múltiplas menções ao tópico, sintetize as informações de forma coerente.
</instrucoes_principais>

<contexto>
{contexto}
</contexto>

<pergunta_usuario>
{pergunta}
</pergunta_usuario>

Resposta:
"""

class SearchDocumentsUseCase:
    """Use case for searching documents using RAG."""
    
    def __init__(self, repository: RepositoryPort, llm: LLMPort):
        self._repository = repository
        self._llm = llm
        self._settings = get_settings()
        self._chain = self._build_chain()
    
    def _build_chain(self):
        """Build the RAG chain with optimized formatting."""
        retriever = self._repository.get_retriever(k=self._settings.retriever_k)
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        llm = self._llm.get_langchain_llm()
        
        def format_docs(docs):
            return "\n".join(
                f"<documento_id={i}>\n{doc.page_content}\n</documento_id={i}>" 
                for i, doc in enumerate(docs)
            )
        
        chain = (
            {
                "contexto": retriever | format_docs, 
                "pergunta": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return chain
    
    def execute(self, query: str) -> SearchResult:
        """
        Search documents and generate response.
        
        Args:
            query: User's question.
            
        Returns:
            SearchResult with the answer.
            
        Raises:
            SearchError: If search fails.
        """
        try:
            # Get relevant chunks
            chunks = self._repository.search(query, k=self._settings.retriever_k)
            
            # Generate response
            answer = self._chain.invoke(query)
            
            return SearchResult(
                query=query,
                answer=answer,
                sources=chunks
            )
            
        except Exception as e:
            raise SearchError(f"Search failed: {str(e)}") from e
    
    def search_sync(self, query: str) -> str:
        """
        Synchronous search that returns just the answer.
        Convenience method for simple use cases.
        
        Args:
            query: User's question.
            
        Returns:
            Answer string.
        """
        result = self.execute(query)
        return result.answer
