"""Catalog API — products list/details. Stateless (state in Postgres + Redis cache)."""
from fastapi import FastAPI, HTTPException
import os

app = FastAPI(title="catalog-api")

# In-memory seed for now (P3 mein Postgres/Redis se replace karenge)
PRODUCTS = {
    "p1": {"id": "p1", "name": "Laptop", "price": 50000, "stock": 5},
    "p2": {"id": "p2", "name": "Mouse", "price": 500, "stock": 50},
    "p3": {"id": "p3", "name": "Keyboard", "price": 1500, "stock": 20},
}


@app.get("/health")          # K8s readiness/liveness probe isse poochega
def health():
    return {"status": "ok", "service": "catalog-api"}


@app.get("/products")
def list_products():
    return {"products": list(PRODUCTS.values())}


@app.get("/products/{pid}")
def get_product(pid: str):
    p = PRODUCTS.get(pid)
    if not p:
        raise HTTPException(404, "Product not found")
    return p
