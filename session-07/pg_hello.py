"""
step1_pg_hello.py — The smallest possible local PostgreSQL connection test.

This is a standalone script — no FastAPI. The goal is to confirm your
local database is running and reachable before touching any web server code.

Run it:
    python step1_pg_hello.py

Expected output:
    Connected to local PostgreSQL!
    Version: PostgreSQL 17.x on ...
    pgcrypto extension: enabled
    users table: exists (0 rows so far)

Environment variables required (.env file):
    DATABASE_URL=postgresql://localhost/pieds_bootcamp
"""

import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def main():
    # url: str = os.environ["DATABASE_URL"]
    url = "postgresql://sde_bootcamp_user:sde_bootcamp_password@localhost:5432/pieds_bootcamp"

    # asyncpg.connect() opens a single connection to PostgreSQL.
    # In main.py we'll use create_pool() for concurrent request handling.
    conn = await asyncpg.connect(url)

    try:
        print("Connected to local PostgreSQL!")

        version = await conn.fetchval("SELECT version()")
        print(f"Version: {version[:50]}...")

        # Check that the pgcrypto extension is active (needed for gen_random_uuid).
        ext = await conn.fetchval(
            "SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'"
        )
        if ext:
            print("pgcrypto extension: enabled")
        else:
            print("pgcrypto extension: NOT found — run: CREATE EXTENSION pgcrypto;")

        # Check the users table.
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'users'
            )
            """
        )
        if table_exists:
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            print(f"users table: exists ({count} rows so far)")
        else:
            print("users table: NOT found — run step2_bcrypt_demo.py which creates it")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
