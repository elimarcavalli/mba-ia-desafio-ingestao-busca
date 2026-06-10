"""
Postgres user repository adapter.

Targets the Chainlit `User` table (created by `src/scripts/init_chainlit_db.py`)
augmented with a `passwordHash` column. Uses psycopg3 (already a project
dependency) via short-lived connections — auth is infrequent and connection
overhead is negligible.
"""
import psycopg

from src.config.settings import get_settings
from src.domain.entities.user import User
from src.domain.ports.user_repository import UserRepositoryPort


class PostgresUserRepository(UserRepositoryPort):
    """psycopg3-backed user repository."""

    def __init__(self) -> None:
        self._dsn = get_settings().database_url

    def get_by_identifier(self, identifier: str) -> User | None:
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT "id", "identifier", "passwordHash" '
                    'FROM "User" WHERE "identifier" = %s LIMIT 1',
                    (identifier,),
                )
                row = cur.fetchone()

        if row is None or row[2] is None:
            return None
        return User(id=row[0], identifier=row[1], password_hash=row[2])

    def create(self, user: User) -> None:
        # ON CONFLICT handles two cases safely:
        #   1. Race between two simultaneous registrations of the same identifier.
        #   2. A pre-existing Chainlit-created row without a passwordHash
        #      (legacy / first-login claim) — we attach the hash to it.
        with psycopg.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO "User" ("id", "identifier", "passwordHash") '
                    'VALUES (%s, %s, %s) '
                    'ON CONFLICT ("identifier") DO UPDATE '
                    'SET "passwordHash" = EXCLUDED."passwordHash", '
                    '    "updatedAt" = NOW()',
                    (user.id, user.identifier, user.password_hash),
                )
            conn.commit()
