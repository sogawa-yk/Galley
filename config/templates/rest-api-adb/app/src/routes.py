"""API routes for {{app_name}}."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/items")
async def list_items() -> dict[str, list]:
    """List all items."""
    return {"items": []}


@router.get("/items/{item_id}")
async def get_item(item_id: str) -> dict[str, str]:
    """Get a specific item."""
    return {"id": item_id, "name": "sample"}
