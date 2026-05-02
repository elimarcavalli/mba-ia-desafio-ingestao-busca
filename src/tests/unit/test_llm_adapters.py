"""
Unit tests for LLM adapters (OpenAI, Google).

LangChain client classes are patched so no real network call is made
and we only validate the adapter wiring (settings → client → response).
"""
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_settings():
    return MagicMock(
        openai_chat_model="gpt-4o-mini",
        openai_api_key="sk-x",
        google_chat_model="gemini-x",
        google_api_key="g-x",
        llm_timeout=42,
    )


class TestOpenAILLMAdapter:
    """Tests for OpenAILLMAdapter."""

    def test_constructor_passes_settings_to_chat_openai(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.openai_llm.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.openai_llm.ChatOpenAI"
        ) as cls:
            from src.infrastructure.adapters.openai_llm import OpenAILLMAdapter

            OpenAILLMAdapter()
            cls.assert_called_once()
            kwargs = cls.call_args.kwargs
            assert kwargs["model"] == "gpt-4o-mini"
            assert kwargs["openai_api_key"] == "sk-x"
            assert kwargs["temperature"] == 0
            assert kwargs["request_timeout"] == 42

    def test_generate_calls_invoke_and_returns_content(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.openai_llm.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.openai_llm.ChatOpenAI"
        ) as cls:
            response = MagicMock()
            response.content = "hello"
            cls.return_value.invoke.return_value = response

            from src.infrastructure.adapters.openai_llm import OpenAILLMAdapter

            adapter = OpenAILLMAdapter()
            out = adapter.generate("prompt")
            assert out == "hello"
            cls.return_value.invoke.assert_called_once_with("prompt")

    def test_get_langchain_llm_returns_underlying(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.openai_llm.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.openai_llm.ChatOpenAI"
        ) as cls:
            cls.return_value = "fake-chat-openai"
            from src.infrastructure.adapters.openai_llm import OpenAILLMAdapter

            adapter = OpenAILLMAdapter()
            assert adapter.get_langchain_llm() == "fake-chat-openai"


class TestGoogleLLMAdapter:
    """Tests for GoogleLLMAdapter."""

    def test_constructor_passes_settings_to_chat_google(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.google_llm.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.google_llm.ChatGoogleGenerativeAI"
        ) as cls:
            from src.infrastructure.adapters.google_llm import GoogleLLMAdapter

            GoogleLLMAdapter()
            cls.assert_called_once()
            kwargs = cls.call_args.kwargs
            assert kwargs["model"] == "gemini-x"
            assert kwargs["google_api_key"] == "g-x"
            assert kwargs["temperature"] == 0
            assert kwargs["timeout"] == 42

    def test_generate_calls_invoke_and_returns_content(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.google_llm.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.google_llm.ChatGoogleGenerativeAI"
        ) as cls:
            response = MagicMock()
            response.content = "world"
            cls.return_value.invoke.return_value = response

            from src.infrastructure.adapters.google_llm import GoogleLLMAdapter

            adapter = GoogleLLMAdapter()
            assert adapter.generate("p") == "world"
            cls.return_value.invoke.assert_called_once_with("p")

    def test_get_langchain_llm_returns_underlying(self, fake_settings):
        with patch(
            "src.infrastructure.adapters.google_llm.get_settings",
            return_value=fake_settings,
        ), patch(
            "src.infrastructure.adapters.google_llm.ChatGoogleGenerativeAI"
        ) as cls:
            cls.return_value = "fake-google"
            from src.infrastructure.adapters.google_llm import GoogleLLMAdapter

            assert GoogleLLMAdapter().get_langchain_llm() == "fake-google"
