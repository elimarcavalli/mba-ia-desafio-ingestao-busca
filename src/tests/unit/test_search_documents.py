"""
Unit tests for SearchDocumentsUseCase.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from langchain_core.documents import Document as LangchainDocument

from src.application.use_cases.search_documents import (
    PROMPT_TEMPLATE,
    SearchDocumentsUseCase,
)
from src.domain.entities.document import DocumentChunk, SearchResult
from src.domain.exceptions import SearchError
from src.domain.ports.llm import LLMPort
from src.domain.ports.repository import RepositoryPort


def _make_llm_mock(invoke_return: str = "Test answer"):
    """Build an LLMPort mock whose underlying LangChain LLM is a Runnable-friendly mock."""
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = invoke_return
    mock = Mock(spec=LLMPort)
    mock.get_langchain_llm.return_value = fake_llm
    return mock, fake_llm


def _make_repo_mock(chunks=None, retriever=None):
    """Build a RepositoryPort mock."""
    mock = Mock(spec=RepositoryPort)
    if chunks is None:
        chunks = [DocumentChunk(content="ctx", metadata={"source_file": "doc.pdf"})]
    mock.search.return_value = chunks
    mock.get_retriever.return_value = retriever if retriever is not None else MagicMock()
    return mock


class TestSearchDocumentsUseCaseConstruction:
    """Tests for construction and chain wiring."""

    def test_get_retriever_called_with_settings_k(self):
        """Constructor must request retriever with retriever_k from settings."""
        repo = _make_repo_mock()
        llm, _ = _make_llm_mock()

        SearchDocumentsUseCase(repo, llm)

        repo.get_retriever.assert_called_once()
        kwargs = repo.get_retriever.call_args.kwargs
        assert kwargs.get("k") == 10

    def test_chain_built_on_init(self):
        """Chain should be built during __init__ (cached)."""
        repo = _make_repo_mock()
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)
        assert use_case._chain is not None


class TestSearchDocumentsExecute:
    """Tests for execute()."""

    def test_returns_search_result_with_query_answer_sources(self):
        """execute() returns SearchResult with proper fields."""
        chunks = [
            DocumentChunk(content="A", metadata={"source_file": "a.pdf"}),
            DocumentChunk(content="B", metadata={"source_file": "b.pdf"}),
        ]
        repo = _make_repo_mock(chunks=chunks)
        llm, _ = _make_llm_mock(invoke_return="The answer")
        use_case = SearchDocumentsUseCase(repo, llm)

        # Stub the chain to avoid running real LangChain runnables
        use_case._chain = MagicMock()
        use_case._chain.invoke.return_value = "The answer"

        result = use_case.execute("What is A?")

        assert isinstance(result, SearchResult)
        assert result.query == "What is A?"
        assert result.answer == "The answer"
        assert result.sources == chunks

    def test_calls_repository_search_with_settings_k(self):
        """execute() must search with k=retriever_k."""
        repo = _make_repo_mock()
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)
        use_case._chain = MagicMock()
        use_case._chain.invoke.return_value = "ok"

        use_case.execute("q")

        repo.search.assert_called_once()
        assert repo.search.call_args.kwargs.get("k") == 15

    def test_chain_invoke_called_with_query(self):
        """Chain.invoke must receive the user query."""
        repo = _make_repo_mock()
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)
        use_case._chain = MagicMock()
        use_case._chain.invoke.return_value = "ok"

        use_case.execute("My question")

        use_case._chain.invoke.assert_called_once_with("My question")

    def test_empty_retrieval_still_returns_result(self):
        """If retriever returns nothing, still call the chain (LLM will say it doesn't know)."""
        repo = _make_repo_mock(chunks=[])
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)
        use_case._chain = MagicMock()
        use_case._chain.invoke.return_value = "I did not find sufficient information"

        result = use_case.execute("q")

        assert result.sources == []
        assert "did not find" in result.answer.lower()

    def test_repository_search_error_wrapped_as_search_error(self):
        """Repository raising should surface as SearchError."""
        repo = _make_repo_mock()
        repo.search.side_effect = RuntimeError("DB down")
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)
        use_case._chain = MagicMock()

        with pytest.raises(SearchError, match="Search failed"):
            use_case.execute("q")

    def test_chain_error_wrapped_as_search_error(self):
        """Chain failure should surface as SearchError (LLM timeout, etc.)."""
        repo = _make_repo_mock()
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)
        use_case._chain = MagicMock()
        use_case._chain.invoke.side_effect = TimeoutError("LLM timed out")

        with pytest.raises(SearchError, match="Search failed"):
            use_case.execute("q")

    def test_search_error_preserves_cause(self):
        """SearchError chains the original exception via __cause__."""
        repo = _make_repo_mock()
        repo.search.side_effect = RuntimeError("orig")
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)

        with pytest.raises(SearchError) as exc_info:
            use_case.execute("q")
        assert isinstance(exc_info.value.__cause__, RuntimeError)


class TestSearchSync:
    """Tests for the convenience search_sync()."""

    def test_search_sync_returns_only_answer_string(self):
        repo = _make_repo_mock()
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)
        use_case._chain = MagicMock()
        use_case._chain.invoke.return_value = "the answer"

        out = use_case.search_sync("q")

        assert out == "the answer"
        assert isinstance(out, str)

    def test_search_sync_propagates_search_error(self):
        repo = _make_repo_mock()
        repo.search.side_effect = RuntimeError("boom")
        llm, _ = _make_llm_mock()
        use_case = SearchDocumentsUseCase(repo, llm)

        with pytest.raises(SearchError):
            use_case.search_sync("q")


class TestPromptAndFormatting:
    """Tests for the prompt template and document formatting."""

    def test_prompt_template_has_required_placeholders(self):
        """Prompt must contain {context} and {question}."""
        assert "{context}" in PROMPT_TEMPLATE
        assert "{question}" in PROMPT_TEMPLATE

    def test_prompt_enforces_grounding_rule(self):
        """Prompt must instruct the model to only use the context."""
        # Cheap but real assertion: the strict-integrity sentinel must be present.
        assert "did not find sufficient information" in PROMPT_TEMPLATE

    def test_format_docs_includes_source_attribution_via_real_chain(self):
        """Exercise the real format_docs closure by running the chain end-to-end
        with a fake retriever and fake LLM that records the prompt it receives."""
        from langchain_core.runnables import RunnableLambda

        # Fake retriever: returns a fixed list of LangchainDocuments.
        fake_docs = [
            LangchainDocument(
                page_content="hello",
                metadata={"source_file": "x.pdf"},
            ),
            LangchainDocument(
                page_content="world",
                metadata={},  # forces "unknown"
            ),
        ]
        fake_retriever = RunnableLambda(lambda _q: fake_docs)

        repo = _make_repo_mock(retriever=fake_retriever)

        # Fake LangChain LLM: any Runnable that captures input.
        captured = {}

        from langchain_core.messages import AIMessage

        def capture_and_respond(prompt_value):
            # ChatPromptTemplate produces a PromptValue; convert to string.
            captured["prompt"] = prompt_value.to_string()
            # Return a real BaseMessage so StrOutputParser can extract content.
            return AIMessage(content="answer")

        fake_llm_runnable = RunnableLambda(capture_and_respond)
        llm = Mock(spec=LLMPort)
        llm.get_langchain_llm.return_value = fake_llm_runnable

        use_case = SearchDocumentsUseCase(repo, llm)
        result = use_case.execute("what?")

        assert result.answer == "answer"
        # Prompt must contain the formatted documents with source attribution.
        prompt_str = captured["prompt"]
        assert '<document source="x.pdf" id=0>' in prompt_str
        assert "hello" in prompt_str
        assert '<document source="unknown" id=1>' in prompt_str
        assert "world" in prompt_str
