#!/usr/bin/env python3
"""
Migration script to fix Chainlit schema constraints.
Removes NOT NULL constraints that cause errors when Chainlit sends NULL values.
"""
import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Migration statements to relax constraints
MIGRATIONS = [
    # Step table - allow NULL for name and type
    'ALTER TABLE "Step" ALTER COLUMN "name" DROP NOT NULL;',
    'ALTER TABLE "Step" ALTER COLUMN "type" DROP NOT NULL;',
    'ALTER TABLE "Step" ALTER COLUMN "threadId" DROP NOT NULL;',
    
    # Element table - allow NULL for name
    'ALTER TABLE "Element" ALTER COLUMN "name" DROP NOT NULL;',
    
    # Feedback table - allow NULL for stepId and value
    'ALTER TABLE "Feedback" ALTER COLUMN "stepId" DROP NOT NULL;',
    'ALTER TABLE "Feedback" ALTER COLUMN "value" DROP NOT NULL;',
]

async def migrate():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found.")
        return False

    print("🔌 Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected!")
        
        print("🛠️ Applying migrations to relax constraints...")
        for migration in MIGRATIONS:
            try:
                await conn.execute(migration)
                print(f"  ✓ Applied: {migration[:50]}...")
            except asyncpg.exceptions.UndefinedColumnError:
                print(f"  ⏭ Column doesn't exist, skipping: {migration[:40]}...")
            except asyncpg.exceptions.UndefinedTableError:
                print(f"  ⏭ Table doesn't exist, skipping: {migration[:40]}...")
            except Exception as e:
                # If constraint already removed, that's fine
                if "does not exist" in str(e).lower():
                    print(f"  ⏭ Already applied: {migration[:40]}...")
                else:
                    print(f"  ⚠ Warning: {e}")
        
        print("✅ Migrations completed!")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(migrate())
