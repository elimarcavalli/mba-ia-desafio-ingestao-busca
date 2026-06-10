"""
Authenticate-or-register user use case.

Single login form acts as both sign-in and sign-up: an unknown identifier
triggers account creation; a known identifier is verified against the stored
password hash. This is the pattern recommended for self-hosted Chainlit apps
without a separate registration page.
"""
import re
import uuid

from src.domain.entities.user import User
from src.domain.exceptions import (
    InvalidCredentialsError,
    InvalidUsernameError,
    WeakPasswordError,
)
from src.domain.ports.password_hasher import PasswordHasherPort
from src.domain.ports.user_repository import UserRepositoryPort


# Permissive on purpose: accepts handles (alice), dotted names (alice.doe),
# emails (alice@example.com) and tagged emails (alice+work@example.com).
# Length 2-64 covers everything from short handles to long emails.
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._@+-]{2,64}$")
_MIN_PASSWORD_LEN = 6


class AuthenticateOrRegisterUserUseCase:
    """Verify an existing user's password, or register them on first login."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        password_hasher: PasswordHasherPort,
    ) -> None:
        self._users = user_repository
        self._hasher = password_hasher

    def execute(self, identifier: str, password: str) -> User:
        identifier = (identifier or "").strip()
        if not _USERNAME_RE.match(identifier):
            raise InvalidUsernameError(
                "Username must be 2-64 characters; allowed: letters, digits, and . _ - + @"
            )
        if not password:
            raise InvalidCredentialsError("Password is required.")

        existing = self._users.get_by_identifier(identifier)
        if existing is not None:
            if not self._hasher.verify(password, existing.password_hash):
                raise InvalidCredentialsError("Invalid username or password.")
            return existing

        if len(password) < _MIN_PASSWORD_LEN:
            raise WeakPasswordError(
                f"Password must be at least {_MIN_PASSWORD_LEN} characters."
            )

        new_user = User(
            id=uuid.uuid4().hex,
            identifier=identifier,
            password_hash=self._hasher.hash(password),
        )
        self._users.create(new_user)
        return new_user
