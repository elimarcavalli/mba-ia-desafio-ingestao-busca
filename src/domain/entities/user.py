"""
User entity.
Represents an authenticated user of the application.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """Authenticated user identified by a unique handle and a password hash."""

    id: str
    identifier: str
    password_hash: str
