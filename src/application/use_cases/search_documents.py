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


PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


class SearchDocumentsUseCase:
    """Use case for searching documents using RAG."""
    
    def __init__(self, repository: RepositoryPort, llm: LLMPort):
        self._repository = repository
        self._llm = llm
        self._settings = get_settings()
        self._chain = self._build_chain()
    
    def _build_chain(self):
        """Build the RAG chain."""
        retriever = self._repository.get_retriever(k=self._settings.retriever_k)
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        llm = self._llm.get_langchain_llm()
        
        def format_docs(docs):
            return "\n\n---\n\n".join(doc.page_content for doc in docs)
        
        chain = (
            {"contexto": retriever | format_docs, "pergunta": RunnablePassthrough()}
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
