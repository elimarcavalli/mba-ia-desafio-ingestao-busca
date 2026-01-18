"""
User authentication service.
Provides secure user registration and login with database persistence.
"""
import hashlib
import os
from typing import Optional
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def get_db_connection():
    """Get database connection."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not configured")
    return await asyncpg.connect(DATABASE_URL)


async def init_users_table():
    """Create users table if it doesn't exist."""
    conn = await get_db_connection()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS "AppUser" (
                "id" SERIAL PRIMARY KEY,
                "username" TEXT NOT NULL UNIQUE,
                "password_hash" TEXT NOT NULL,
                "role" TEXT NOT NULL DEFAULT 'user',
                "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
    finally:
        await conn.close()


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    # Use a simple salt based on username for demo
    # In production, use bcrypt or argon2
    salt = os.getenv("CHAINLIT_AUTH_SECRET", "default-salt")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


async def create_user(username: str, password: str, role: str = "user") -> bool:
    """
    Create a new user.
    Returns True if successful, False if user already exists.
    """
    conn = await get_db_connection()
    try:
        password_hash = hash_password(password)
        await conn.execute(
            """
            INSERT INTO "AppUser" ("username", "password_hash", "role")
            VALUES ($1, $2, $3)
            """,
            username, password_hash, role
        )
        return True
    except asyncpg.exceptions.UniqueViolationError:
        return False  # User already exists
    finally:
        await conn.close()


async def verify_user(username: str, password: str) -> Optional[dict]:
    """
    Verify user credentials.
    Returns user data if valid, None otherwise.
    """
    conn = await get_db_connection()
    try:
        password_hash = hash_password(password)
        row = await conn.fetchrow(
            """
            SELECT "id", "username", "role" 
            FROM "AppUser" 
            WHERE "username" = $1 AND "password_hash" = $2
            """,
            username, password_hash
        )
        if row:
            return {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"]
            }
        return None
    finally:
        await conn.close()


async def user_exists(username: str) -> bool:
    """Check if a user exists."""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            'SELECT 1 FROM "AppUser" WHERE "username" = $1',
            username
        )
        return row is not None
    finally:
        await conn.close()


async def ensure_default_admin():
    """Create default admin user if no users exist."""
    conn = await get_db_connection()
    try:
        count = await conn.fetchval('SELECT COUNT(*) FROM "AppUser"')
        if count == 0:
            await create_user("admin", "admin", role="admin")
            print("  ✓ Created default admin user (admin/admin)")
    except Exception:
        pass  # Table might not exist yet
    finally:
        await conn.close()
