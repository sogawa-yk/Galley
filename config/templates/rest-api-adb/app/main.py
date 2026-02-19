"""{{app_name}} - REST API Application."""

from fastapi import FastAPI

from src.db import get_db_pool
from src.routes import router

app = FastAPI(title="{{app_name}}", version="0.1.0")
app.include_router(router)


@app.on_event("startup")
async def startup() -> None:
    """Initialize database connection pool."""
    await get_db_pool()


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "app": "{{app_name}}"}
