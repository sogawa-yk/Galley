"""Inventory API - FastAPI Application"""
import os

from fastapi import FastAPI

from .database import engine, Base
from .routers import products, categories, inventory
from .seed import seed_data

app = FastAPI(
    title="Inventory API",
    description="商品の在庫数をリアルタイムで管理するREST API",
    version="1.0.0",
)

app.include_router(products.router)
app.include_router(categories.router)
app.include_router(inventory.router)


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    seed_data()


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
