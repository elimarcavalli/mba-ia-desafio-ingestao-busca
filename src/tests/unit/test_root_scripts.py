"""
Unit tests for the CLI entry points (src/ingest.py, src/chat.py).
"""
from unittest.mock import Mock, patch

import pytest

from src.domain.entities.document import DocumentChunk, SearchResult
from src.infrastructure.factories.provider_factory import ProviderFactory
from src import ingest as ingest_script
from src import chat as chat_script


@pytest.fixture(autouse=True)
def _reset_factory():
    ProviderFactory.reset()
    yield
    ProviderFactory.reset()


class TestIngestScript:
    """Tests for src/ingest.py."""

    def test_ingest_default_uses_pdf_path_setting(self, mock_repository, mock_document_loader, tmp_path, monkeypatch):
        doc = tmp_path / "document.pdf"
        doc.write_text("content")
        monkeypatch.setattr(ingest_script, "PROJECT_ROOT", str(tmp_path))

        # Real settings: pdf_path defaults to "document.pdf" (also set in .env)
        with patch.object(ProviderFactory, "get_repository", return_value=mock_repository), \
             patch.object(ProviderFactory, "get_document_loader", return_value=mock_document_loader):
            result = ingest_script.ingest()

        assert result.name == "document.pdf"
        mock_document_loader.load.assert_called_once()
        _, kwargs = mock_repository.add_documents.call_args
        assert kwargs.get("clear_existing") is True

    def test_ingest_explicit_relative_path_resolves_to_project_root(self, mock_repository, mock_document_loader, tmp_path, monkeypatch):
        doc = tmp_path / "other.pdf"
        doc.write_text("content")
        monkeypatch.setattr(ingest_script, "PROJECT_ROOT", str(tmp_path))

        with patch.object(ProviderFactory, "get_repository", return_value=mock_repository), \
             patch.object(ProviderFactory, "get_document_loader", return_value=mock_document_loader):
            result = ingest_script.ingest("other.pdf")

        assert result.name == "other.pdf"
        loaded_path = mock_document_loader.load.call_args[0][0]
        assert loaded_path == str(doc)

    def test_ingest_append_keeps_existing(self, mock_repository, mock_document_loader, tmp_path, monkeypatch):
        doc = tmp_path / "extra.pdf"
        doc.write_text("content")
        monkeypatch.setattr(ingest_script, "PROJECT_ROOT", str(tmp_path))

        with patch.object(ProviderFactory, "get_repository", return_value=mock_repository), \
             patch.object(ProviderFactory, "get_document_loader", return_value=mock_document_loader):
            ingest_script.ingest("extra.pdf", append=True)

        _, kwargs = mock_repository.add_documents.call_args
        assert kwargs.get("clear_existing") is False

    def test_main_append_flag_sets_append(self, mock_repository, mock_document_loader, tmp_path, monkeypatch):
        doc = tmp_path / "extra.pdf"
        doc.write_text("content")
        monkeypatch.setattr(ingest_script, "PROJECT_ROOT", str(tmp_path))
        monkeypatch.setattr("sys.argv", ["ingest.py", "extra.pdf", "--append"])

        with patch.object(ProviderFactory, "get_repository", return_value=mock_repository), \
             patch.object(ProviderFactory, "get_document_loader", return_value=mock_document_loader):
            ingest_script.main()

        _, kwargs = mock_repository.add_documents.call_args
        assert kwargs.get("clear_existing") is False

    def test_ingest_missing_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ingest_script, "PROJECT_ROOT", str(tmp_path))

        with pytest.raises(FileNotFoundError, match="Document not found"):
            ingest_script.ingest("missing.pdf")

    def test_main_exits_nonzero_on_failure(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(ingest_script, "PROJECT_ROOT", str(tmp_path))
        monkeypatch.setattr("sys.argv", ["ingest.py", "missing.pdf"])

        with pytest.raises(SystemExit) as exc:
            ingest_script.main()

        assert exc.value.code == 1
        assert "Ingestion failed" in capsys.readouterr().out


class TestChatScript:
    """Tests for src/chat.py."""

    def test_ask_returns_answer(self):
        use_case = Mock()
        use_case.execute.return_value = SearchResult(
            query="q",
            answer="The answer",
            sources=[DocumentChunk(content="c", metadata={})],
        )

        assert chat_script.ask(use_case, "q") == "The answer"
        use_case.execute.assert_called_once_with("q")

    def test_main_one_shot_prints_answer_and_exits(self, monkeypatch, capsys):
        use_case = Mock()
        use_case.execute.return_value = SearchResult(query="q", answer="42", sources=[])
        monkeypatch.setattr("sys.argv", ["chat.py", "what", "is", "it?"])

        with patch.object(chat_script, "build_search_use_case", return_value=use_case):
            chat_script.main()

        out = capsys.readouterr().out
        assert "42" in out
        use_case.execute.assert_called_once_with("what is it?")

    def test_main_exits_nonzero_on_failure(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["chat.py", "question"])

        with patch.object(chat_script, "build_search_use_case", side_effect=RuntimeError("db down")), \
             pytest.raises(SystemExit) as exc:
            chat_script.main()

        assert exc.value.code == 1
        assert "db down" in capsys.readouterr().out

    def test_chat_loop_answers_then_exits(self, monkeypatch, capsys):
        use_case = Mock()
        use_case.execute.return_value = SearchResult(query="q", answer="hello!", sources=[])
        answers = iter(["my question", "exit"])
        monkeypatch.setattr("builtins.input", lambda *a: next(answers))

        chat_script.chat_loop(use_case)

        out = capsys.readouterr().out
        assert "hello!" in out
        assert "See you later" in out
        use_case.execute.assert_called_once_with("my question")
