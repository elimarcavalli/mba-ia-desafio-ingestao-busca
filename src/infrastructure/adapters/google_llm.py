"""
Google LLM adapter.
Implements LLMPort for Google Generative AI.
"""
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.settings import get_settings
from src.domain.ports.llm import LLMPort


class GoogleLLMAdapter(LLMPort):
    """Google Generative AI LLM adapter."""
    
    def __init__(self):
        settings = get_settings()
        self._llm = ChatGoogleGenerativeAI(
            model=settings.google_chat_model,
            google_api_key=settings.google_api_key,
            temperature=0,
            timeout=settings.llm_timeout,
        )
    
    def generate(self, prompt: str) -> str:
        """Generate response for prompt."""
        response = self._llm.invoke(prompt)
        return response.content
    
    def get_langchain_llm(self) -> ChatGoogleGenerativeAI:
        """Get LangChain LLM object."""
        return self._llm
