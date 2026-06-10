"""
Argon2id password hasher adapter.

Argon2id is the OWASP-recommended password hash. The library defaults
(`argon2-cffi`) are tuned to current guidance.
"""
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from src.domain.ports.password_hasher import PasswordHasherPort


class Argon2PasswordHasher(PasswordHasherPort):
    """Argon2id-based implementation of PasswordHasherPort."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, password)
        except (VerifyMismatchError, InvalidHashError, VerificationError):
            return False
