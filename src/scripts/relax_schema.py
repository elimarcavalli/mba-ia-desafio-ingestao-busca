import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Schema without Foreign Key constraints
SCHEMA = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS "Feedback" CASCADE;
DROP TABLE IF EXISTS "Element" CASCADE;
DROP TABLE IF EXISTS "Step" CASCADE;
DROP TABLE IF EXISTS "Thread" CASCADE;
DROP TABLE IF EXISTS "User" CASCADE;

-- User Table
CREATE TABLE "User" (
    "id" TEXT PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Thread Table
CREATE TABLE "Thread" (
    "id" TEXT PRIMARY KEY,
    "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "deletedAt" TIMESTAMPTZ,
    "name" TEXT,
    "userId" TEXT, -- Removed FK
    "userIdentifier" TEXT,
    "tags" TEXT[],
    "metadata" JSONB NOT NULL DEFAULT '{}'
);

-- Step Table
CREATE TABLE "Step" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "threadId" TEXT NOT NULL, -- Removed FK
    "parentId" TEXT, -- Removed FK
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

-- Element Table
CREATE TABLE "Element" (
    "id" TEXT PRIMARY KEY,
    "threadId" TEXT, -- Removed FK
    "stepId" TEXT, -- Removed FK
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "mime" TEXT,
    "name" TEXT NOT NULL,
    "objectKey" TEXT,
    "url" TEXT,
    "chainlitKey" TEXT,
    "display" TEXT,
    "size" TEXT,
    "language" TEXT,
    "page" INT,
    "props" JSONB
);

-- Feedback Table
CREATE TABLE "Feedback" (
    "id" TEXT PRIMARY KEY,
    "stepId" TEXT NOT NULL, -- Removed FK
    "name" TEXT,
    "value" FLOAT NOT NULL,
    "comment" TEXT
);

-- Indexes for performance (still needed)
CREATE INDEX idx_thread_user_id ON "Thread"("userId");
CREATE INDEX idx_step_thread_id ON "Step"("threadId");
CREATE INDEX idx_element_thread_id ON "Element"("threadId");
"""

async def relax_db():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found.")
        return

    print(f"🔌 Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected!")
        
        print("🛠️ Recreating schema without FKs...")
        await conn.execute(SCHEMA)
        print("✅ Schema relaxed successfully!")
        
        await conn.close()
    except Exception as e:
        print(f"❌ Error relaxing database: {e}")

if __name__ == "__main__":
    asyncio.run(relax_db())
