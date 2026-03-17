"""Inventory record endpoints for stock in/out management."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product, InventoryRecord
from ..schemas import InventoryRecordCreate, InventoryRecordResponse

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/", response_model=List[InventoryRecordResponse])
def list_records(product_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(InventoryRecord)
    if product_id is not None:
        query = query.filter(InventoryRecord.product_id == product_id)
    return query.order_by(InventoryRecord.created_at.desc()).all()


@router.post("/", response_model=InventoryRecordResponse, status_code=201)
def create_record(data: InventoryRecordCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if data.record_type == "out" and product.quantity < data.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {product.quantity}, Requested: {data.quantity}",
        )

    # Update product quantity
    if data.record_type == "in":
        product.quantity += data.quantity
    else:
        product.quantity -= data.quantity

    record = InventoryRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{record_id}", response_model=InventoryRecordResponse)
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(InventoryRecord).filter(InventoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record
