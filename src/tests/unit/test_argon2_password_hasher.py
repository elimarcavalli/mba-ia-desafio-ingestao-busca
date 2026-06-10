"""
Unit tests for the Argon2 password hasher adapter.
"""
import pytest

from src.infrastructure.adapters.argon2_password_hasher import Argon2PasswordHasher


@pytest.fixture
def hasher() -> Argon2PasswordHasher:
    return Argon2PasswordHasher()


def test_hash_then_verify_succeeds(hasher):
    h = hasher.hash("correct horse battery staple")
    assert h.startswith("$argon2"), "Argon2 PHC string expected"
    assert hasher.verify("correct horse battery staple", h) is True


def test_verify_rejects_wrong_password(hasher):
    h = hasher.hash("correct horse battery staple")
    assert hasher.verify("wrong password", h) is False


def test_verify_returns_false_on_invalid_hash(hasher):
    assert hasher.verify("anything", "not-a-real-hash") is False


def test_hash_includes_random_salt(hasher):
    h1 = hasher.hash("same-password")
    h2 = hasher.hash("same-password")
    assert h1 != h2, "Salt must make hashes non-deterministic"
