"""
Unit tests for Chainlit pure helpers.

We don't boot Chainlit — only the pure helpers that don't depend on its runtime.
"""
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock


def _ensure_chainlit_stub():
    """Stub the chainlit module so importing chainlit_app doesn't blow up.

    Chainlit pulls in a server runtime; for unit-testing pure helpers we
    don't need it. A minimal stub satisfies the import-time decorators.
    """
    if "chainlit" in sys.modules:
        return

    cl_stub = MagicMock(name="chainlit_stub")

    # Decorators must return the function unchanged so imports succeed.
    def passthrough_decorator(*dargs, **dkwargs):
        # Support both @decorator and @decorator(...) forms.
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
    cl_stub.make_async = lambda fn: fn

    sys.modules["chainlit"] = cl_stub


_ensure_chainlit_stub()


from src.presentation.web import chainlit_app  # noqa: E402


class TestSupportedMimes:
    """SUPPORTED_MIMES drives the file picker filter."""

    def test_is_list_of_strings(self):
        assert isinstance(chainlit_app.SUPPORTED_MIMES, list)
        assert all(isinstance(m, str) for m in chainlit_app.SUPPORTED_MIMES)
        assert len(chainlit_app.SUPPORTED_MIMES) > 0

    def test_includes_all_required_mimes(self):
        required = {
            "application/pdf",
            "text/plain",
            "text/csv",
            "text/html",
            "application/json",
            "text/markdown",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        assert required.issubset(set(chainlit_app.SUPPORTED_MIMES))


class TestIsSupportedFile:
    """_is_supported_file checks the original filename's extension."""

    def test_supported_pdf(self):
        el = SimpleNamespace(name="report.pdf")
        assert chainlit_app._is_supported_file(el) is True

    def test_supported_md(self):
        el = SimpleNamespace(name="readme.md")
        assert chainlit_app._is_supported_file(el) is True

    def test_supported_uppercase_extension(self):
        el = SimpleNamespace(name="DOC.PDF")
        assert chainlit_app._is_supported_file(el) is True

    def test_unsupported_extension(self):
        el = SimpleNamespace(name="image.png")
        assert chainlit_app._is_supported_file(el) is False

    def test_no_name_returns_false(self):
        el = SimpleNamespace(name=None)
        assert chainlit_app._is_supported_file(el) is False

    def test_empty_name_returns_false(self):
        el = SimpleNamespace(name="")
        assert chainlit_app._is_supported_file(el) is False

    def test_no_extension_returns_false(self):
        el = SimpleNamespace(name="Makefile")
        assert chainlit_app._is_supported_file(el) is False
