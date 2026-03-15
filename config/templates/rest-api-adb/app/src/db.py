"""Database connection management for {{db_name}}.

Protected file - do not modify.
"""

import logging
import os

import oracledb

logger = logging.getLogger("{{app_name}}.db")

# Protected file - do not modify
DB_DSN = os.environ.get("DATABASE_DSN", "")
DB_USER = os.environ.get("DATABASE_USER", "")
DB_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
DB_WALLET_DIR = os.environ.get("DATABASE_WALLET_DIR", "/app/wallet")

_pool: oracledb.AsyncConnectionPool | None = None


async def get_db_pool() -> oracledb.AsyncConnectionPool:
    """Get or create the database connection pool.

    Returns:
        AsyncConnectionPool: Oracle ADB connection pool.

    Raises:
        RuntimeError: If database configuration is missing.
    """
    global _pool
    if _pool is not None:
        return _pool

    if not DB_DSN:
        raise RuntimeError(
            "DATABASE_DSN is not set. "
            "Set it to your ADB connection string (e.g., '(description=...)')."
        )

    try:
        # mTLS wallet-based connection (typical for ADB)
        if os.path.isdir(DB_WALLET_DIR):
            oracledb.init_oracle_client(config_dir=DB_WALLET_DIR)

        _pool = oracledb.create_pool_async(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN,
            min=2,
            max=10,
            increment=1,
        )
        logger.info("Database connection pool created (min=2, max=10)")
        return _pool
    except Exception:
        logger.exception("Failed to create database connection pool")
        raise


async def check_db_health() -> bool:
    """Check database connectivity.

    Returns:
        True if the database is reachable, False otherwise.
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT 1 FROM DUAL")
            await cursor.close()
        return True
    except Exception:
        logger.warning("Database health check failed", exc_info=True)
        return False


async def close_db_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")
