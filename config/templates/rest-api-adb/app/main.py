"""{{app_name}} - REST API Application."""

import logging
import sys

from fastapi import FastAPI

from src.db import check_db_health, close_db_pool, get_db_pool
from src.routes import router

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("{{app_name}}")

app = FastAPI(title="{{app_name}}", version="0.1.0")
app.include_router(router)


@app.on_event("startup")
async def startup() -> None:
    """Initialize database connection pool."""
    logger.info("Starting {{app_name}}")
    try:
        await get_db_pool()
        logger.info("Database pool initialized")
    except Exception:
        logger.exception("Failed to initialize database pool (app will start without DB)")


@app.on_event("shutdown")
async def shutdown() -> None:
    """Clean up resources."""
    logger.info("Shutting down {{app_name}}")
    await close_db_pool()


@app.get("/health")
async def health() -> dict[str, str | bool]:
    """Health check endpoint with database connectivity status."""
    db_ok = await check_db_health()
    return {
        "status": "ok" if db_ok else "degraded",
        "app": "{{app_name}}",
        "database": db_ok,
    }
