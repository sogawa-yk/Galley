"""Seed data for demo/testing purposes."""
from .database import SessionLocal
from .models import Category, Product


def seed_data():
    """Insert sample data if the database is empty."""
    db = SessionLocal()
    try:
        if db.query(Category).count() > 0:
            return  # Already seeded

        # Categories
        electronics = Category(name="Electronics", description="電子機器・デバイス")
        clothing = Category(name="Clothing", description="衣類・アパレル")
        food = Category(name="Food & Beverage", description="食品・飲料")
        db.add_all([electronics, clothing, food])
        db.flush()

        # Products
        products = [
            Product(
                name="Wireless Mouse",
                sku="ELEC-001",
                description="ワイヤレスマウス Bluetooth対応",
                price=2980.0,
                quantity=150,
                category_id=electronics.id,
            ),
            Product(
                name="USB-C Cable",
                sku="ELEC-002",
                description="USB-C充電ケーブル 1m",
                price=980.0,
                quantity=300,
                category_id=electronics.id,
            ),
            Product(
                name="T-Shirt (M)",
                sku="CLTH-001",
                description="コットンTシャツ Mサイズ",
                price=1500.0,
                quantity=200,
                category_id=clothing.id,
            ),
            Product(
                name="Green Tea 500ml",
                sku="FOOD-001",
                description="緑茶ペットボトル 500ml",
                price=150.0,
                quantity=500,
                category_id=food.id,
            ),
            Product(
                name="Notebook",
                sku="MISC-001",
                description="A4ノート 100ページ",
                price=350.0,
                quantity=80,
            ),
        ]
        db.add_all(products)
        db.commit()
    finally:
        db.close()
