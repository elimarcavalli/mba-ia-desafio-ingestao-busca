"""
OpenAI LLM adapter.
Implements LLMPort for OpenAI.
"""
from langchain_openai import ChatOpenAI

from src.config.settings import get_settings
from src.domain.ports.llm import LLMPort


class OpenAILLMAdapter(LLMPort):
    """OpenAI LLM adapter."""
    
    def __init__(self):
        settings = get_settings()
        self._llm = ChatOpenAI(
            model=settings.openai_chat_model,
            openai_api_key=settings.openai_api_key,
            temperature=0,
            request_timeout=settings.llm_timeout,
        )
    
    def generate(self, prompt: str) -> str:
        """Generate response for prompt."""
        response = self._llm.invoke(prompt)
        return response.content
    
    def get_langchain_llm(self) -> ChatOpenAI:
        """Get LangChain LLM object."""
        return self._llm
