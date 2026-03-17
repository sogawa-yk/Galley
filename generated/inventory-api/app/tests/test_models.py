"""Unit tests for data models."""
from ..models import Category, Product, InventoryRecord


def test_category_creation(db_session):
    cat = Category(name="Test Category", description="A test")
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    assert cat.id is not None
    assert cat.name == "Test Category"
    assert cat.created_at is not None


def test_product_creation(db_session):
    product = Product(name="Widget", sku="W-001", price=100.0, quantity=10)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    assert product.id is not None
    assert product.quantity == 10
    assert product.sku == "W-001"


def test_product_category_relationship(db_session):
    cat = Category(name="Gadgets")
    db_session.add(cat)
    db_session.flush()
    product = Product(name="Gadget A", sku="G-001", price=50.0, category_id=cat.id)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    assert product.category.name == "Gadgets"
    assert len(cat.products) == 1


def test_inventory_record_creation(db_session):
    product = Product(name="Item", sku="I-001", price=10.0, quantity=5)
    db_session.add(product)
    db_session.flush()
    record = InventoryRecord(
        product_id=product.id, record_type="in", quantity=10, note="Initial stock"
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    assert record.id is not None
    assert record.record_type == "in"
    assert record.quantity == 10
