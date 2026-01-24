import sys
import io

# Ensure UTF-8 output on Windows (cp1252 can't handle emojis)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import asyncio
import os
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Chainlit Database URL (standard postgresql:// format)
# We handle the case where it might be in DATABASE_URL or CHAINLIT_DATABASE_URL
# but our previous fix put the standard URL in DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# DDL Schema derived from chainlit.data.chainlit_data_layer.py source code
SCHEMA = """
-- Enable UUID extension just in case, though usually generated in app
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Table
CREATE TABLE IF NOT EXISTS "User" (
    "id" TEXT PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Thread Table (relaxed constraints for Chainlit compatibility)
CREATE TABLE IF NOT EXISTS "Thread" (
    "id" TEXT PRIMARY KEY,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "deletedAt" TIMESTAMPTZ,
    "name" TEXT,
    "userId" TEXT,  -- Removed FK for async insert order
    "userIdentifier" TEXT,
    "tags" TEXT[],
    "metadata" JSONB NOT NULL DEFAULT '{}'
);

-- Step Table (relaxed constraints for Chainlit compatibility)
CREATE TABLE IF NOT EXISTS "Step" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT,  -- Chainlit sometimes sends NULL
    "type" TEXT,  -- Chainlit sometimes sends NULL
    "threadId" TEXT,  -- Removed FK for async insert order
    "parentId" TEXT,  -- Removed FK for async insert order
    "disableFeedback" BOOLEAN NOT NULL DEFAULT false,
    "streaming" BOOLEAN NOT NULL DEFAULT false,
    "waitForAnswer" BOOLEAN DEFAULT false,
    "isError" BOOLEAN DEFAULT false,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "input" TEXT,
    "output" TEXT,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "startTime" TIMESTAMPTZ,
    "endTime" TIMESTAMPTZ,
    "generation" JSONB,
    "showInput" TEXT,
    "language" TEXT,
    "indent" INT
);

-- Element Table (relaxed constraints for Chainlit compatibility)
CREATE TABLE IF NOT EXISTS "Element" (
    "id" TEXT PRIMARY KEY,
    "threadId" TEXT,  -- Removed FK for async insert order
    "stepId" TEXT,  -- Removed FK for async insert order
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "mime" TEXT,
    "name" TEXT,  -- Chainlit sometimes sends NULL
    "objectKey" TEXT,
    "url" TEXT,
    "chainlitKey" TEXT,
    "display" TEXT,
    "size" TEXT,
    "language" TEXT,
    "page" INT,
    "props" JSONB
);

-- Feedback Table (relaxed constraints for Chainlit compatibility)
CREATE TABLE IF NOT EXISTS "Feedback" (
    "id" TEXT PRIMARY KEY,
    "stepId" TEXT,  -- Removed FK for async insert order
    "name" TEXT,
    "value" FLOAT,  -- Chainlit sometimes sends NULL
    "comment" TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_thread_user_id ON "Thread"("userId");
CREATE INDEX IF NOT EXISTS idx_step_thread_id ON "Step"("threadId");
CREATE INDEX IF NOT EXISTS idx_element_thread_id ON "Element"("threadId");
"""

async def init_db():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment.")
        return

    print(f"🔌 Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected!")
        
        print("🛠️ Creating schema tables...")
        await conn.execute(SCHEMA)
        print("✅ All tables created successfully!")
        
        await conn.close()
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
