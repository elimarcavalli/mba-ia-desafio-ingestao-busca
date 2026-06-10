"""
Unit tests for Chainlit async handlers.

We stub the chainlit module before import (see test_chainlit_helpers.py) and
exercise the handlers with controlled mocks for the user session + Provider
factory.
"""
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _ensure_chainlit_stub():
    """Stub chainlit so the module imports cleanly."""
    if "chainlit" in sys.modules:
        return

    cl_stub = MagicMock(name="chainlit_stub")

    def passthrough_decorator(*dargs, **dkwargs):
        if dargs and callable(dargs[0]) and len(dargs) == 1 and not dkwargs:
            return dargs[0]
        def _wrap(fn):
            return fn
        return _wrap

    cl_stub.on_chat_resume = passthrough_decorator
    cl_stub.on_chat_start = passthrough_decorator
    cl_stub.on_message = passthrough_decorator
    cl_stub.action_callback = passthrough_decorator
    cl_stub.set_starters = passthrough_decorator
    cl_stub.password_auth_callback = passthrough_decorator
    cl_stub.User = MagicMock(name="chainlit_User")
    cl_stub.Action = MagicMock()
    cl_stub.Message = MagicMock()
    cl_stub.AskFileMessage = MagicMock()
    cl_stub.Starter = MagicMock()
    cl_stub.Thread = MagicMock()
    cl_stub.user_session = MagicMock()
    cl_stub.context = SimpleNamespace(session=SimpleNamespace(thread_id=None))
    def make_async(fn):
        async def _wrapped(*a, **kw):
            return fn(*a, **kw)
        return _wrapped

    cl_stub.make_async = make_async

    sys.modules["chainlit"] = cl_stub


_ensure_chainlit_stub()

from src.presentation.web import chainlit_app  # noqa: E402


# --- helpers ---------------------------------------------------------------


def _setup_user_session(initial=None):
    """Patch chainlit_app.cl.user_session with an in-memory dict."""
    store = dict(initial or {})

    def get(k):
        return store.get(k)

    def set_(k, v):
        store[k] = v

    chainlit_app.cl.user_session.get = MagicMock(side_effect=get)
    chainlit_app.cl.user_session.set = MagicMock(side_effect=set_)
    return store


def _patch_message():
    """Patch chainlit_app.cl.Message to capture sent content."""
    sent = []

    class FakeMessage:
        def __init__(self, content="", actions=None):
            self.content = content
            self.actions = actions
            sent.append(self)

        async def send(self):
            return None

        async def update(self):
            return None

    chainlit_app.cl.Message = FakeMessage
    return sent


# --- tests -----------------------------------------------------------------


class TestShowPdfList:
    """Tests for show_pdf_list()."""

    @pytest.mark.asyncio
    async def test_empty_library_message(self):
        _setup_user_session({"pdf_data": {}})
        sent = _patch_message()
        await chainlit_app.show_pdf_list()
        assert any("No documents loaded" in m.content for m in sent)

    @pytest.mark.asyncio
    async def test_lists_documents_with_chunk_counts(self):
        _setup_user_session({"pdf_data": {"a.pdf": 5, "b.md": 3}})
        sent = _patch_message()
        await chainlit_app.show_pdf_list()
        assert len(sent) == 1
        msg = sent[0]
        assert "a.pdf" in msg.content
        assert "5 chunks" in msg.content
        assert "b.md" in msg.content
        assert "Total" in msg.content
        # Two delete buttons + one refresh = 3 actions
        assert msg.actions is not None
        assert len(msg.actions) == 3


class TestIngestFiles:
    """Tests for _ingest_files() — the shared upload pipeline."""

    @pytest.mark.asyncio
    async def test_ingest_single_file_updates_session_and_creates_search(self):
        _setup_user_session({"pdf_data": {}})
        _patch_message()

        fake_file = SimpleNamespace(name="report.md", path="/tmp/xxx")

        with patch.object(chainlit_app, "process_file", new=AsyncMock(return_value=(7, "report.md"))), \
             patch.object(chainlit_app, "_create_search_use_case", return_value="search-uc"), \
             patch.object(chainlit_app, "update_thread_metadata", new=AsyncMock()):

            await chainlit_app._ingest_files([fake_file])

        # pdf_data must contain the new file with its chunk count
        pdf_data = chainlit_app.cl.user_session.get("pdf_data")
        assert pdf_data == {"report.md": 7}
        # search_use_case must be set
        assert chainlit_app.cl.user_session.get("search_use_case") == "search-uc"

    @pytest.mark.asyncio
    async def test_ingest_failure_does_not_crash(self):
        _setup_user_session({"pdf_data": {}})
        _patch_message()

        fake_file = SimpleNamespace(name="bad.pdf", path="/tmp/xxx")

        with patch.object(chainlit_app, "process_file", new=AsyncMock(side_effect=RuntimeError("boom"))), \
             patch.object(chainlit_app, "_create_search_use_case", return_value="search-uc"), \
             patch.object(chainlit_app, "update_thread_metadata", new=AsyncMock()):

            # Must not raise
            await chainlit_app._ingest_files([fake_file])

        # pdf_data still empty since the only ingestion failed
        assert chainlit_app.cl.user_session.get("pdf_data") == {}

    @pytest.mark.asyncio
    async def test_clear_existing_only_on_first_file_when_library_is_empty(self):
        _setup_user_session({"pdf_data": {}})
        _patch_message()

        files = [
            SimpleNamespace(name="a.pdf", path="/tmp/a"),
            SimpleNamespace(name="b.pdf", path="/tmp/b"),
        ]
        process = AsyncMock(side_effect=[(1, "a.pdf"), (2, "b.pdf")])

        with patch.object(chainlit_app, "process_file", new=process), \
             patch.object(chainlit_app, "_create_search_use_case", return_value="search-uc"), \
             patch.object(chainlit_app, "update_thread_metadata", new=AsyncMock()):
            await chainlit_app._ingest_files(files)

        # First call must have clear_first=True; second must be False.
        first_kwargs = process.call_args_list[0]
        second_kwargs = process.call_args_list[1]
        # process_file(file_el, clear_first) → positional args
        assert first_kwargs.args[1] is True
        assert second_kwargs.args[1] is False

    @pytest.mark.asyncio
    async def test_clear_existing_false_when_library_has_items(self):
        _setup_user_session({"pdf_data": {"existing.pdf": 5}})
        _patch_message()

        files = [SimpleNamespace(name="new.pdf", path="/tmp/new")]
        process = AsyncMock(return_value=(3, "new.pdf"))

        with patch.object(chainlit_app, "process_file", new=process), \
             patch.object(chainlit_app, "_create_search_use_case", return_value="search-uc"), \
             patch.object(chainlit_app, "update_thread_metadata", new=AsyncMock()):
            await chainlit_app._ingest_files(files)

        assert process.call_args.args[1] is False


class TestHandleDeletePdf:
    """Tests for handle_delete_pdf action callback."""

    @pytest.mark.asyncio
    async def test_delete_removes_from_library_and_keeps_search_when_others_remain(self):
        _setup_user_session({"pdf_data": {"a.pdf": 5, "b.pdf": 3}, "search_use_case": "old"})
        _patch_message()

        fake_repo = MagicMock()
        fake_repo.delete_by_source.return_value = 5

        with patch.object(chainlit_app.ProviderFactory, "get_repository", return_value=fake_repo), \
             patch.object(chainlit_app, "_create_search_use_case", return_value="new-search"), \
             patch.object(chainlit_app, "update_thread_metadata", new=AsyncMock()), \
             patch.object(chainlit_app, "show_pdf_list", new=AsyncMock()):

            action = MagicMock()
            action.payload = {"pdf_name": "a.pdf"}
            await chainlit_app.handle_delete_pdf(action)

        pdf_data = chainlit_app.cl.user_session.get("pdf_data")
        assert pdf_data == {"b.pdf": 3}
        # search_use_case rebuilt because library not empty
        assert chainlit_app.cl.user_session.get("search_use_case") == "new-search"
        fake_repo.delete_by_source.assert_called_once_with("a.pdf")

    @pytest.mark.asyncio
    async def test_delete_clears_search_when_library_empty(self):
        _setup_user_session({"pdf_data": {"only.pdf": 5}, "search_use_case": "old"})
        _patch_message()

        fake_repo = MagicMock()
        fake_repo.delete_by_source.return_value = 5

        with patch.object(chainlit_app.ProviderFactory, "get_repository", return_value=fake_repo), \
             patch.object(chainlit_app, "_create_search_use_case", return_value="new-search"), \
             patch.object(chainlit_app, "update_thread_metadata", new=AsyncMock()), \
             patch.object(chainlit_app, "show_pdf_list", new=AsyncMock()):

            action = MagicMock()
            action.payload = {"pdf_name": "only.pdf"}
            await chainlit_app.handle_delete_pdf(action)

        assert chainlit_app.cl.user_session.get("pdf_data") == {}
        assert chainlit_app.cl.user_session.get("search_use_case") is None

    @pytest.mark.asyncio
    async def test_delete_repo_error_handled(self):
        _setup_user_session({"pdf_data": {"a.pdf": 5}})
        sent = _patch_message()

        fake_repo = MagicMock()
        fake_repo.delete_by_source.side_effect = RuntimeError("DB fail")

        with patch.object(chainlit_app.ProviderFactory, "get_repository", return_value=fake_repo):
            action = MagicMock()
            action.payload = {"pdf_name": "a.pdf"}
            await chainlit_app.handle_delete_pdf(action)

        # Error message must be sent
        assert any("Oops" in m.content for m in sent)


class TestOnChatResume:
    """Tests for on_chat_resume()."""

    @pytest.mark.asyncio
    async def test_resume_with_pdf_data_restores_session(self):
        _setup_user_session({})
        _patch_message()

        with patch.object(chainlit_app, "_create_search_use_case", return_value="search-uc"):
            await chainlit_app.on_chat_resume(
                {"metadata": {"pdf_data": {"x.pdf": 4}}}
            )

        assert chainlit_app.cl.user_session.get("pdf_data") == {"x.pdf": 4}
        assert chainlit_app.cl.user_session.get("search_use_case") == "search-uc"

    @pytest.mark.asyncio
    async def test_resume_with_no_pdf_data(self):
        _setup_user_session({})
        sent = _patch_message()

        await chainlit_app.on_chat_resume({"metadata": {}})

        assert chainlit_app.cl.user_session.get("pdf_data") == {}
        assert any("no documents are loaded" in m.content for m in sent)

    @pytest.mark.asyncio
    async def test_resume_search_uc_creation_failure(self):
        _setup_user_session({})
        sent = _patch_message()

        with patch.object(
            chainlit_app, "_create_search_use_case", side_effect=RuntimeError("boom")
        ):
            await chainlit_app.on_chat_resume(
                {"metadata": {"pdf_data": {"x.pdf": 4}}}
            )

        assert any("Error restoring context" in m.content for m in sent)


class TestUpdateThreadMetadata:
    """Tests for update_thread_metadata()."""

    @pytest.mark.asyncio
    async def test_no_thread_id_silent_skip(self):
        _setup_user_session({"pdf_data": {"a": 1}})
        # No thread id available
        chainlit_app.cl.context = SimpleNamespace(session=SimpleNamespace(thread_id=None))
        # Must not raise
        await chainlit_app.update_thread_metadata()

    @pytest.mark.asyncio
    async def test_no_session_attribute_silent_skip(self):
        _setup_user_session({"pdf_data": {"a": 1}})
        chainlit_app.cl.context = SimpleNamespace()  # no .session
        await chainlit_app.update_thread_metadata()

    @pytest.mark.asyncio
    async def test_thread_update_called_with_metadata(self):
        _setup_user_session({"pdf_data": {"a": 1}})
        chainlit_app.cl.context = SimpleNamespace(
            session=SimpleNamespace(thread_id="tid-1")
        )

        thread_inst = MagicMock()
        thread_inst.update = AsyncMock()
        chainlit_app.cl.Thread = MagicMock(return_value=thread_inst)

        await chainlit_app.update_thread_metadata()
        thread_inst.update.assert_awaited_once()


class TestProcessFile:
    """Tests for process_file() — wires factory + ingest use case."""

    @pytest.mark.asyncio
    async def test_returns_chunk_count_and_filename(self):
        fake_doc = MagicMock()
        fake_doc.chunk_count = 5

        fake_uc = MagicMock()
        fake_uc.execute.return_value = fake_doc

        with patch.object(chainlit_app.ProviderFactory, "get_repository", return_value="repo"), \
             patch.object(chainlit_app.ProviderFactory, "get_document_loader", return_value="loader"), \
             patch.object(chainlit_app, "IngestDocumentUseCase", return_value=fake_uc):

            file_el = SimpleNamespace(name="r.pdf", path="/tmp/abc")
            count, name = await chainlit_app.process_file(file_el, clear_first=True)

        assert count == 5
        assert name == "r.pdf"
        fake_uc.execute.assert_called_once_with(
            "/tmp/abc", source_name="r.pdf", clear_existing=True
        )


class TestOnMessageRouter:
    """Tests for the @cl.on_message handler (command routing + search)."""

    @pytest.mark.asyncio
    async def test_attached_supported_files_trigger_ingest(self):
        _setup_user_session({"pdf_data": {}})
        _patch_message()

        message = MagicMock()
        message.elements = [SimpleNamespace(name="report.pdf")]
        message.content = ""

        ingest_calls = AsyncMock()
        with patch.object(chainlit_app, "_ingest_files", new=ingest_calls):
            await chainlit_app.main(message)

        ingest_calls.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_attached_files_with_question_ingests_then_answers(self):
        fake_search = MagicMock()
        fake_result = MagicMock()
        fake_result.answer = "The document says..."
        fake_search.execute.return_value = fake_result
        _setup_user_session({"pdf_data": {}})
        sent = _patch_message()

        message = MagicMock()
        message.elements = [SimpleNamespace(name="report.pdf")]
        message.content = "What does the report say?"

        async def fake_ingest(_files):
            chainlit_app.cl.user_session.set("pdf_data", {"report.pdf": 7})
            chainlit_app.cl.user_session.set("search_use_case", fake_search)

        with patch.object(chainlit_app, "_ingest_files", new=fake_ingest):
            await chainlit_app.main(message)

        fake_search.execute.assert_called_once_with("What does the report say?")
        assert any(m.content == "The document says..." for m in sent)

    @pytest.mark.asyncio
    async def test_attached_unsupported_files_ignored(self):
        _setup_user_session({"pdf_data": {}})
        _patch_message()

        message = MagicMock()
        message.elements = [SimpleNamespace(name="image.png")]
        message.content = "/help"

        ingest_calls = AsyncMock()
        with patch.object(chainlit_app, "_ingest_files", new=ingest_calls):
            await chainlit_app.main(message)

        ingest_calls.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "cmd", ["/files", "/arquivos", "/pdfs", "/listar", "/FILES", "  /files  "]
    )
    async def test_files_command_aliases_show_list(self, cmd):
        _setup_user_session({"pdf_data": {}})
        _patch_message()

        message = MagicMock()
        message.elements = []
        message.content = cmd

        show = AsyncMock()
        with patch.object(chainlit_app, "show_pdf_list", new=show):
            await chainlit_app.main(message)

        show.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_help_command_sends_help_message(self):
        _setup_user_session({"pdf_data": {}})
        sent = _patch_message()

        message = MagicMock()
        message.elements = []
        message.content = "/help"

        await chainlit_app.main(message)
        assert any("Smart Document Assistant" in m.content for m in sent)

    @pytest.mark.asyncio
    async def test_examples_command_sends_examples_message(self):
        _setup_user_session({"pdf_data": {}})
        sent = _patch_message()

        message = MagicMock()
        message.elements = []
        message.content = "/examples"

        await chainlit_app.main(message)
        assert any("Question Ideas" in m.content for m in sent)

    @pytest.mark.asyncio
    async def test_no_search_use_case_prompts_upload(self):
        _setup_user_session({"pdf_data": {}, "search_use_case": None})
        sent = _patch_message()

        message = MagicMock()
        message.elements = []
        message.content = "What is RAG?"

        await chainlit_app.main(message)
        assert any("No documents loaded yet" in m.content for m in sent)

    @pytest.mark.asyncio
    async def test_search_executes_and_returns_answer(self):
        fake_search = MagicMock()
        fake_result = MagicMock()
        fake_result.answer = "RAG is..."
        fake_search.execute.return_value = fake_result
        _setup_user_session(
            {"pdf_data": {"x.pdf": 5}, "search_use_case": fake_search}
        )

        sent = []

        class FakeMessage:
            def __init__(self, content="", actions=None):
                self.content = content
                self.actions = actions
                sent.append(self)

            async def send(self):
                return None

            async def update(self):
                return None

        chainlit_app.cl.Message = FakeMessage

        message = MagicMock()
        message.elements = []
        message.content = "What is RAG?"

        await chainlit_app.main(message)
        # Last message must contain the answer
        assert any(m.content == "RAG is..." for m in sent)

    @pytest.mark.asyncio
    async def test_search_error_sent_to_user(self):
        fake_search = MagicMock()
        fake_search.execute.side_effect = RuntimeError("LLM down")
        _setup_user_session(
            {"pdf_data": {"x.pdf": 5}, "search_use_case": fake_search}
        )
        sent = _patch_message()

        message = MagicMock()
        message.elements = []
        message.content = "anything"

        await chainlit_app.main(message)
        assert any("Oops" in m.content for m in sent)


class TestSetStarters:
    """Tests for set_starters() — returns the welcome screen entries."""

    @pytest.mark.asyncio
    async def test_returns_three_starters(self):
        # Replace Starter with a recording stub so we can count
        chainlit_app.cl.Starter = MagicMock(side_effect=lambda **kw: kw)
        out = await chainlit_app.set_starters()
        assert len(out) == 3
        labels = [s["label"] for s in out]
        assert any("Upload" in l for l in labels)
        assert any("How does it work" in l for l in labels)
        assert any("example questions" in l for l in labels)


class TestStart:
    """Tests for the @cl.on_chat_start handler."""

    @pytest.mark.asyncio
    async def test_start_initializes_pdf_data(self):
        store = _setup_user_session({})
        await chainlit_app.start()
        assert store["pdf_data"] == {}


class TestActionCallbacksBasic:
    """Tests for trivial action callbacks that just call show_pdf_list."""

    @pytest.mark.asyncio
    async def test_handle_refresh_list_calls_show(self):
        show = AsyncMock()
        with patch.object(chainlit_app, "show_pdf_list", new=show):
            await chainlit_app.handle_refresh_list(MagicMock())
        show.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_show_pdfs_calls_show(self):
        show = AsyncMock()
        with patch.object(chainlit_app, "show_pdf_list", new=show):
            await chainlit_app.handle_show_pdfs(MagicMock())
        show.assert_awaited_once()


class TestUploadCommand:
    """Tests for the /upload command path inside on_message()."""

    @pytest.mark.asyncio
    async def test_upload_no_files_selected(self):
        _setup_user_session({"pdf_data": {}})
        sent = _patch_message()

        ask = MagicMock()
        ask.send = AsyncMock(return_value=None)
        chainlit_app.cl.AskFileMessage = MagicMock(return_value=ask)

        message = MagicMock()
        message.elements = []
        message.content = "/upload"

        ingest = AsyncMock()
        with patch.object(chainlit_app, "_ingest_files", new=ingest):
            await chainlit_app.main(message)

        ingest.assert_not_awaited()
        assert any("No files selected" in m.content for m in sent)

    @pytest.mark.asyncio
    async def test_upload_with_files_calls_ingest_and_shows_summary(self):
        _setup_user_session({"pdf_data": {}})
        sent = _patch_message()

        files = [SimpleNamespace(name="r.pdf", path="/tmp/x")]
        ask = MagicMock()
        ask.send = AsyncMock(return_value=files)
        chainlit_app.cl.AskFileMessage = MagicMock(return_value=ask)

        async def fake_ingest(_files):
            chainlit_app.cl.user_session.set("pdf_data", {"r.pdf": 7})

        message = MagicMock()
        message.elements = []
        message.content = "/upload"

        with patch.object(chainlit_app, "_ingest_files", new=fake_ingest):
            await chainlit_app.main(message)

        # Summary message must reflect the new state
        assert any("All set" in m.content and "1 document" in m.content for m in sent)
