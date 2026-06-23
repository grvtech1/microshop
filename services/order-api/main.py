"""Order API — orders (Postgres). Calls catalog-api (INTER-SERVICE) for price/stock."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import psycopg2
import httpx

app = FastAPI(title="order-api")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "microshop")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASS = os.environ.get("DB_PASSWORD", "")
# Inter-service: catalog-api ko SERVICE NAME se call (DNS — IP nahi!)
CATALOG_URL = os.environ.get("CATALOG_URL", "http://catalog-api:8000")


def db():
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


class OrderIn(BaseModel):
    product_id: str
    qty: int = 1


@app.on_event("startup")
def init():
    conn = db(); cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, product_id TEXT, qty INT, total INT)")
    conn.commit(); conn.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "order-api"}


@app.post("/orders")
def create_order(body: OrderIn):
    # ⭐ INTER-SERVICE CALL — catalog-api se price/stock lo (service DNS)
    try:
        resp = httpx.get(f"{CATALOG_URL}/products/{body.product_id}", timeout=5)
    except Exception:
        raise HTTPException(503, "catalog-api unreachable")
    if resp.status_code == 404:
        raise HTTPException(404, "Product not found")
    product = resp.json()
    if product["stock"] < body.qty:
        raise HTTPException(409, "Not enough stock")

    total = product["price"] * body.qty
    conn = db(); cur = conn.cursor()
    cur.execute("INSERT INTO orders (product_id,qty,total) VALUES (%s,%s,%s) RETURNING id",
                (body.product_id, body.qty, total))
    oid = cur.fetchone()[0]; conn.commit(); conn.close()
    return {"order_id": oid, "product": product["name"], "qty": body.qty, "total": total}


@app.get("/orders")
def list_orders():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id,product_id,qty,total FROM orders ORDER BY id DESC LIMIT 20")
    rows = cur.fetchall(); conn.close()
    return {"orders": [{"id": r[0], "product_id": r[1], "qty": r[2], "total": r[3]} for r in rows]}
