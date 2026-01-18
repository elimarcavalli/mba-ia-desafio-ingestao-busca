"""
LLM port (interface).
Defines the contract for LLM providers.
"""
from abc import ABC, abstractmethod


class LLMPort(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a response for the given prompt.
        
        Args:
            prompt: The input prompt.
            
        Returns:
            Generated text response.
        """
        pass
    
    @abstractmethod
    def get_langchain_llm(self):
        """
        Get the underlying LangChain LLM object.
        Required for compatibility with LangChain chains.
        
        Returns:
            LangChain LLM instance.
        """
        pass
