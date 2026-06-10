"""
Password hasher port (interface).
Defines the contract for hashing and verifying passwords.
"""
from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    """Abstract interface for password hashing."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a hash string suitable for storage."""

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """Return True if the password matches the stored hash."""
