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
You are an AI Assistant Expert in Corporate Semantic Search. Your role is to provide precise, deterministic answers based **strictly** on the retrieved documents provided in the context.

### **Operational Guidelines**

1. **Source of Truth:** Use **ONLY** the information provided within the `<context>` tags. Do not use external knowledge or facts not present in the text.
2. **Strict Integrity:** If the information is missing, incomplete, or cannot be logically deduced from the context, you **MUST** respond with: "I did not find sufficient information in the documents to answer this question."
3. **No Preambles:** Do not use conversational filler such as "Based on the documents provided..." or "According to the text...". Start the answer immediately.
4. **Synthesis:** If the topic is mentioned in multiple parts of the context, consolidate the information into a coherent and structured response.
5. **Language Match:** You must respond in the **same language** used by the user in the `<user_question>`.
6. **Reasoning Process:** Before providing the final answer, perform a brief internal check (Chain-of-Thought) to ensure every claim in your response is mapped to a specific piece of information in the context.

### **Negative Constraints**

* **NO** Hallucinations: Do not invent dates, names, or technical details.
* **NO** Outside Knowledge: If the context says the sky is green, your answer must reflect that the sky is green.
* **NO** Assumptions: Do not infer intent or meaning that is not explicitly stated.

---

### **Context**

{context}

---

### **User Question**

{question}

---

**Answer:**

---

Would you like me to adjust the **strictness level** of the fallback message or modify the **output format** (e.g., JSON or specific bullet point styles)?
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
                f"<document_id={i}>\n{doc.page_content}\n</document_id={i}>" 
                for i, doc in enumerate(docs)
            )
        
        chain = (
            {
                "context": retriever | format_docs, 
                "question": RunnablePassthrough()
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
