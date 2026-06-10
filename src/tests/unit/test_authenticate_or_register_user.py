"""
Unit tests for AuthenticateOrRegisterUserUseCase.
"""
from unittest.mock import MagicMock

import pytest

from src.application.use_cases.authenticate_or_register_user import (
    AuthenticateOrRegisterUserUseCase,
)
from src.domain.entities.user import User
from src.domain.exceptions import (
    InvalidCredentialsError,
    InvalidUsernameError,
    WeakPasswordError,
)
from src.domain.ports.password_hasher import PasswordHasherPort
from src.domain.ports.user_repository import UserRepositoryPort


def _make_use_case(
    existing: User | None = None,
    verify_returns: bool = True,
):
    repo = MagicMock(spec=UserRepositoryPort)
    repo.get_by_identifier.return_value = existing

    hasher = MagicMock(spec=PasswordHasherPort)
    hasher.hash.return_value = "hashed-pw"
    hasher.verify.return_value = verify_returns

    return AuthenticateOrRegisterUserUseCase(repo, hasher), repo, hasher


class TestExistingUser:
    def test_returns_user_when_password_matches(self):
        existing = User(id="u1", identifier="alice", password_hash="stored-hash")
        use_case, repo, hasher = _make_use_case(existing=existing, verify_returns=True)

        result = use_case.execute("alice", "correct-password")

        assert result is existing
        repo.get_by_identifier.assert_called_once_with("alice")
        hasher.verify.assert_called_once_with("correct-password", "stored-hash")
        repo.create.assert_not_called()
        hasher.hash.assert_not_called()

    def test_raises_invalid_credentials_on_password_mismatch(self):
        existing = User(id="u1", identifier="alice", password_hash="stored-hash")
        use_case, repo, hasher = _make_use_case(existing=existing, verify_returns=False)

        with pytest.raises(InvalidCredentialsError):
            use_case.execute("alice", "wrong")

        repo.create.assert_not_called()


class TestNewUser:
    def test_registers_when_identifier_does_not_exist(self):
        use_case, repo, hasher = _make_use_case(existing=None)

        result = use_case.execute("bob", "supersecret")

        assert result.identifier == "bob"
        assert result.password_hash == "hashed-pw"
        assert result.id  # uuid hex assigned
        hasher.hash.assert_called_once_with("supersecret")
        repo.create.assert_called_once()
        created = repo.create.call_args[0][0]
        assert created.identifier == "bob"
        assert created.password_hash == "hashed-pw"

    def test_rejects_weak_password_on_registration(self):
        use_case, repo, hasher = _make_use_case(existing=None)

        with pytest.raises(WeakPasswordError):
            use_case.execute("bob", "abc")

        hasher.hash.assert_not_called()
        repo.create.assert_not_called()


class TestIdentifierValidation:
    @pytest.mark.parametrize(
        "bad_identifier",
        ["", "a", "x" * 65, "user name", "üser", "<script>", "user!", "user/"],
    )
    def test_rejects_invalid_identifiers(self, bad_identifier):
        use_case, repo, _ = _make_use_case(existing=None)

        with pytest.raises(InvalidUsernameError):
            use_case.execute(bad_identifier, "supersecret")

        repo.get_by_identifier.assert_not_called()

    @pytest.mark.parametrize(
        "good_identifier",
        [
            "ab",
            "alice",
            "alice.doe",
            "alice_doe",
            "alice-doe",
            "alice@example.com",
            "alice+work@example.com",
            "elimar.cavalli@gmail.com",
        ],
    )
    def test_accepts_handles_dots_and_emails(self, good_identifier):
        use_case, repo, _ = _make_use_case(existing=None)

        use_case.execute(good_identifier, "supersecret")

        repo.get_by_identifier.assert_called_once_with(good_identifier)

    def test_strips_surrounding_whitespace(self):
        use_case, repo, _ = _make_use_case(existing=None)

        use_case.execute("  alice  ", "supersecret")

        repo.get_by_identifier.assert_called_once_with("alice")


class TestPasswordValidation:
    def test_rejects_empty_password(self):
        use_case, repo, _ = _make_use_case(existing=None)

        with pytest.raises(InvalidCredentialsError):
            use_case.execute("alice", "")

        repo.get_by_identifier.assert_not_called()

    def test_existing_user_login_skips_password_strength_policy(self):
        # Legacy account with weak password should still be allowed to authenticate
        # — strength policy only applies at registration.
        existing = User(id="u1", identifier="alice", password_hash="legacy")
        use_case, _, hasher = _make_use_case(existing=existing, verify_returns=True)

        result = use_case.execute("alice", "shortpw")

        assert result is existing
        hasher.verify.assert_called_once_with("shortpw", "legacy")
