"""Integration tests for API endpoints."""


# --- Health ---
def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- Categories ---
def test_create_category(client):
    resp = client.post("/categories/", json={"name": "Books", "description": "Book category"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Books"
    assert data["id"] is not None


def test_list_categories(client):
    client.post("/categories/", json={"name": "A"})
    client.post("/categories/", json={"name": "B"})
    resp = client.get("/categories/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_category(client):
    create = client.post("/categories/", json={"name": "Toys"})
    cid = create.json()["id"]
    resp = client.get(f"/categories/{cid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Toys"


def test_get_category_not_found(client):
    resp = client.get("/categories/9999")
    assert resp.status_code == 404


def test_update_category(client):
    create = client.post("/categories/", json={"name": "Old"})
    cid = create.json()["id"]
    resp = client.put(f"/categories/{cid}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_delete_category(client):
    create = client.post("/categories/", json={"name": "Temp"})
    cid = create.json()["id"]
    resp = client.delete(f"/categories/{cid}")
    assert resp.status_code == 204
    resp = client.get(f"/categories/{cid}")
    assert resp.status_code == 404


# --- Products ---
def test_create_product(client):
    resp = client.post(
        "/products/",
        json={"name": "Pen", "sku": "PEN-001", "price": 200.0, "quantity": 50},
    )
    assert resp.status_code == 201
    assert resp.json()["sku"] == "PEN-001"


def test_list_products(client):
    client.post("/products/", json={"name": "A", "sku": "A-1", "price": 1.0})
    resp = client.get("/products/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_product(client):
    create = client.post("/products/", json={"name": "X", "sku": "X-1", "price": 5.0})
    pid = create.json()["id"]
    resp = client.get(f"/products/{pid}")
    assert resp.status_code == 200


def test_get_product_not_found(client):
    resp = client.get("/products/9999")
    assert resp.status_code == 404


def test_update_product(client):
    create = client.post("/products/", json={"name": "Y", "sku": "Y-1", "price": 10.0})
    pid = create.json()["id"]
    resp = client.put(f"/products/{pid}", json={"name": "Y Updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Y Updated"


def test_delete_product(client):
    create = client.post("/products/", json={"name": "Z", "sku": "Z-1", "price": 3.0})
    pid = create.json()["id"]
    resp = client.delete(f"/products/{pid}")
    assert resp.status_code == 204


# --- Inventory ---
def test_create_inventory_record_in(client):
    prod = client.post("/products/", json={"name": "P", "sku": "P-1", "price": 1.0, "quantity": 0})
    pid = prod.json()["id"]
    resp = client.post(
        "/inventory/",
        json={"product_id": pid, "record_type": "in", "quantity": 20, "note": "Restock"},
    )
    assert resp.status_code == 201
    # Verify quantity updated
    product = client.get(f"/products/{pid}").json()
    assert product["quantity"] == 20


def test_create_inventory_record_out(client):
    prod = client.post("/products/", json={"name": "Q", "sku": "Q-1", "price": 1.0, "quantity": 50})
    pid = prod.json()["id"]
    resp = client.post(
        "/inventory/",
        json={"product_id": pid, "record_type": "out", "quantity": 10},
    )
    assert resp.status_code == 201
    product = client.get(f"/products/{pid}").json()
    assert product["quantity"] == 40


def test_inventory_insufficient_stock(client):
    prod = client.post("/products/", json={"name": "R", "sku": "R-1", "price": 1.0, "quantity": 5})
    pid = prod.json()["id"]
    resp = client.post(
        "/inventory/",
        json={"product_id": pid, "record_type": "out", "quantity": 100},
    )
    assert resp.status_code == 400
    assert "Insufficient" in resp.json()["detail"]


def test_inventory_product_not_found(client):
    resp = client.post(
        "/inventory/",
        json={"product_id": 9999, "record_type": "in", "quantity": 1},
    )
    assert resp.status_code == 404


def test_list_inventory_records(client):
    prod = client.post("/products/", json={"name": "S", "sku": "S-1", "price": 1.0, "quantity": 100})
    pid = prod.json()["id"]
    client.post("/inventory/", json={"product_id": pid, "record_type": "in", "quantity": 5})
    client.post("/inventory/", json={"product_id": pid, "record_type": "out", "quantity": 2})
    resp = client.get("/inventory/", params={"product_id": pid})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_inventory_record(client):
    prod = client.post("/products/", json={"name": "T", "sku": "T-1", "price": 1.0, "quantity": 10})
    pid = prod.json()["id"]
    rec = client.post("/inventory/", json={"product_id": pid, "record_type": "in", "quantity": 3})
    rid = rec.json()["id"]
    resp = client.get(f"/inventory/{rid}")
    assert resp.status_code == 200


def test_get_inventory_record_not_found(client):
    resp = client.get("/inventory/9999")
    assert resp.status_code == 404


def test_invalid_record_type(client):
    prod = client.post("/products/", json={"name": "U", "sku": "U-1", "price": 1.0, "quantity": 10})
    pid = prod.json()["id"]
    resp = client.post(
        "/inventory/",
        json={"product_id": pid, "record_type": "invalid", "quantity": 1},
    )
    assert resp.status_code == 422  # Validation error
