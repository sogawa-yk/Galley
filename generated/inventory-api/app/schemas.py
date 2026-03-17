"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Category ---
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Product ---
class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    sku: str = Field(..., max_length=50)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    quantity: int = Field(default=0, ge=0)
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    sku: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Inventory Record ---
class InventoryRecordBase(BaseModel):
    product_id: int
    record_type: str = Field(..., pattern="^(in|out)$")
    quantity: int = Field(..., gt=0)
    note: Optional[str] = None


class InventoryRecordCreate(InventoryRecordBase):
    pass


class InventoryRecordResponse(InventoryRecordBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
