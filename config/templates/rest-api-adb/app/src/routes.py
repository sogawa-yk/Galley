"""API routes for {{app_name}}."""

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from src.auth import verify_token

logger = logging.getLogger("{{app_name}}.routes")

router = APIRouter(prefix="/api/v1")


# --- Request/Response Models ---


class ItemCreate(BaseModel):
    """Request model for creating an item."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)


class ItemResponse(BaseModel):
    """Response model for a single item."""

    id: str
    name: str
    description: str = ""


class ItemListResponse(BaseModel):
    """Response model for item list."""

    items: list[ItemResponse]


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str


# --- Auth dependency ---


async def _get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """Extract and verify the bearer token from Authorization header.

    Args:
        authorization: Authorization header value.

    Returns:
        Token claims dict.

    Raises:
        HTTPException: If token is missing or invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[len("Bearer "):]
    claims = await verify_token(token)
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return claims


# --- Routes ---


@router.get("/items", response_model=ItemListResponse)
async def list_items() -> dict[str, Any]:
    """List all items.

    Returns:
        List of items from the database.
    """
    try:
        # TODO: Replace with actual database query
        return {"items": []}
    except Exception:
        logger.exception("Failed to list items")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str) -> dict[str, Any]:
    """Get a specific item by ID.

    Args:
        item_id: The item identifier.

    Returns:
        The requested item.

    Raises:
        HTTPException: If the item is not found.
    """
    try:
        # TODO: Replace with actual database query
        # Example: raise HTTPException(status_code=404, detail="Item not found")
        return {"id": item_id, "name": "sample", "description": ""}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get item %s", item_id)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate) -> dict[str, Any]:
    """Create a new item.

    Args:
        item: The item data (validated by Pydantic).

    Returns:
        The created item with generated ID.
    """
    try:
        import uuid

        new_id = str(uuid.uuid4())[:8]
        logger.info("Created item: id=%s, name=%s", new_id, item.name)
        # TODO: Replace with actual database insert
        return {"id": new_id, "name": item.name, "description": item.description}
    except Exception:
        logger.exception("Failed to create item")
        raise HTTPException(status_code=500, detail="Internal server error")
