"""
Unit tests for CLI helpers.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.adapters.document_loader import MultiFormatDocumentLoader
from src.infrastructure.factories.provider_factory import ProviderFactory
from src.presentation.cli import chat as cli_chat


@pytest.fixture(autouse=True)
def _reset_factory():
    ProviderFactory.reset()
    yield
    ProviderFactory.reset()


@pytest.fixture
def doc_dir(tmp_path):
    """Create a tmp dir with a mix of supported and unsupported files."""
    (tmp_path / "report.pdf").write_text("x")
    (tmp_path / "notes.md").write_text("# n")
    (tmp_path / "data.csv").write_text("a,b")
    (tmp_path / "image.png").write_text("not a real png")
    (tmp_path / "binary.exe").write_text("not exe")
    (tmp_path / "no_ext_file").write_text("x")
    return tmp_path


class TestListDocuments:
    """Tests for list_documents()."""

    def test_filters_supported_extensions(self, doc_dir):
        out = cli_chat.list_documents(str(doc_dir))
        assert set(out) == {"report.pdf", "notes.md", "data.csv"}

    def test_returns_sorted(self, doc_dir):
        out = cli_chat.list_documents(str(doc_dir))
        assert out == sorted(out)

    def test_empty_dir_returns_empty(self, tmp_path):
        out = cli_chat.list_documents(str(tmp_path))
        assert out == []

    def test_only_unsupported_files_returns_empty(self, tmp_path):
        (tmp_path / "x.png").write_text("a")
        (tmp_path / "y.exe").write_text("b")
        out = cli_chat.list_documents(str(tmp_path))
        assert out == []


class TestSelectDocument:
    """Tests for select_document() interactive helper."""

    def test_no_documents_returns_none(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        out = cli_chat.select_document()
        assert out is None
        captured = capsys.readouterr()
        assert "No supported files" in captured.out

    def test_valid_choice_returns_filename(self, doc_dir, monkeypatch):
        monkeypatch.chdir(doc_dir)
        with patch("builtins.input", return_value="1"):
            out = cli_chat.select_document()
        # First sorted entry — depends on ordering
        sorted_files = sorted(["report.pdf", "notes.md", "data.csv"])
        assert out == sorted_files[0]

    def test_empty_input_returns_none(self, doc_dir, monkeypatch):
        monkeypatch.chdir(doc_dir)
        with patch("builtins.input", return_value=""):
            assert cli_chat.select_document() is None

    def test_keyboard_interrupt_returns_none(self, doc_dir, monkeypatch):
        monkeypatch.chdir(doc_dir)
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            assert cli_chat.select_document() is None

    def test_invalid_then_valid_input(self, doc_dir, monkeypatch, capsys):
        monkeypatch.chdir(doc_dir)
        # Sequence: non-numeric → out-of-range → valid
        inputs = iter(["abc", "999", "1"])
        with patch("builtins.input", side_effect=lambda *_: next(inputs)):
            out = cli_chat.select_document()
        assert out is not None
        captured = capsys.readouterr()
        assert "Invalid number" in captured.out or "valid number" in captured.out


class TestMain:
    """Tests for the CLI main() entry point."""

    def test_no_documents_returns_early(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        cli_chat.main()
        captured = capsys.readouterr()
        assert "See you later" in captured.out

    def test_full_session_ingest_then_exit(self, doc_dir, monkeypatch, capsys):
        monkeypatch.chdir(doc_dir)

        real_loader = MultiFormatDocumentLoader()
        fake_doc = MagicMock(chunk_count=4)
        fake_ingest = MagicMock()
        fake_ingest.execute.return_value = fake_doc

        with patch.object(ProviderFactory, "get_repository"), \
             patch.object(ProviderFactory, "get_llm"), \
             patch.object(ProviderFactory, "get_document_loader", return_value=real_loader), \
             patch.object(cli_chat, "IngestDocumentUseCase", return_value=fake_ingest), \
             patch.object(cli_chat, "SearchDocumentsUseCase") as search_cls, \
             patch("builtins.input", side_effect=["1", "exit"]):

            search_cls.return_value = MagicMock()
            cli_chat.main()

        captured = capsys.readouterr()
        assert "Ingestion complete" in captured.out
        assert "4 chunks" in captured.out
        assert "Chat started" in captured.out
        assert "See you later" in captured.out

    def test_chat_loop_processes_question(self, doc_dir, monkeypatch, capsys):
        monkeypatch.chdir(doc_dir)

        real_loader = MultiFormatDocumentLoader()
        fake_ingest = MagicMock()
        fake_ingest.execute.return_value = MagicMock(chunk_count=2)

        result = MagicMock(answer="the answer is 42")
        search_inst = MagicMock()
        search_inst.execute.return_value = result

        with patch.object(ProviderFactory, "get_repository"), \
             patch.object(ProviderFactory, "get_llm"), \
             patch.object(ProviderFactory, "get_document_loader", return_value=real_loader), \
             patch.object(cli_chat, "IngestDocumentUseCase", return_value=fake_ingest), \
             patch.object(cli_chat, "SearchDocumentsUseCase", return_value=search_inst), \
             patch("builtins.input", side_effect=["1", "what?", "quit"]):
            cli_chat.main()

        captured = capsys.readouterr()
        assert "the answer is 42" in captured.out

    def test_keyboard_interrupt_in_chat_exits(self, doc_dir, monkeypatch, capsys):
        monkeypatch.chdir(doc_dir)

        real_loader = MultiFormatDocumentLoader()
        fake_ingest = MagicMock()
        fake_ingest.execute.return_value = MagicMock(chunk_count=2)

        with patch.object(ProviderFactory, "get_repository"), \
             patch.object(ProviderFactory, "get_llm"), \
             patch.object(ProviderFactory, "get_document_loader", return_value=real_loader), \
             patch.object(cli_chat, "IngestDocumentUseCase", return_value=fake_ingest), \
             patch.object(cli_chat, "SearchDocumentsUseCase"), \
             patch("builtins.input", side_effect=["1", KeyboardInterrupt]):
            cli_chat.main()

        captured = capsys.readouterr()
        assert "See you later" in captured.out

    def test_empty_question_continues_loop(self, doc_dir, monkeypatch, capsys):
        monkeypatch.chdir(doc_dir)

        real_loader = MultiFormatDocumentLoader()
        fake_ingest = MagicMock()
        fake_ingest.execute.return_value = MagicMock(chunk_count=2)

        result = MagicMock(answer="A")
        search_inst = MagicMock()
        search_inst.execute.return_value = result

        with patch.object(ProviderFactory, "get_repository"), \
             patch.object(ProviderFactory, "get_llm"), \
             patch.object(ProviderFactory, "get_document_loader", return_value=real_loader), \
             patch.object(cli_chat, "IngestDocumentUseCase", return_value=fake_ingest), \
             patch.object(cli_chat, "SearchDocumentsUseCase", return_value=search_inst), \
             patch("builtins.input", side_effect=["1", "", "real question", "exit"]):
            cli_chat.main()

        assert search_inst.execute.call_count == 1

    def test_ingest_error_exits_with_code_1(self, doc_dir, monkeypatch):
        monkeypatch.chdir(doc_dir)

        real_loader = MultiFormatDocumentLoader()
        fake_ingest = MagicMock()
        fake_ingest.execute.side_effect = RuntimeError("disk full")

        with patch.object(ProviderFactory, "get_repository"), \
             patch.object(ProviderFactory, "get_llm"), \
             patch.object(ProviderFactory, "get_document_loader", return_value=real_loader), \
             patch.object(cli_chat, "IngestDocumentUseCase", return_value=fake_ingest), \
             patch("builtins.input", return_value="1"):
            with pytest.raises(SystemExit) as exc_info:
                cli_chat.main()
            assert exc_info.value.code == 1
