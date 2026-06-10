"""
User repository port (interface).
Defines the contract for user persistence.
"""
from abc import ABC, abstractmethod

from src.domain.entities.user import User


class UserRepositoryPort(ABC):
    """Abstract interface for user storage."""

    @abstractmethod
    def get_by_identifier(self, identifier: str) -> User | None:
        """Return the user with the given identifier, or None if it does not exist."""

    @abstractmethod
    def create(self, user: User) -> None:
        """Persist a new user. Implementations must be safe against identifier races."""
