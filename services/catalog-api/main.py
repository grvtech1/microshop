"""Catalog API — products (Postgres) + cache (Redis). Stateless service."""
from fastapi import FastAPI, HTTPException
import os, json
import psycopg2
import redis

app = FastAPI(title="catalog-api")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "microshop")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASS = os.environ.get("DB_PASSWORD", "")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")

SEED = [
    ("p1", "Laptop", 50000, 5),
    ("p2", "Mouse", 500, 50),
    ("p3", "Keyboard", 1500, 20),
]


def db():
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


def cache():
    try:
        return redis.Redis(host=REDIS_HOST, port=6379, socket_connect_timeout=2)
    except Exception:
        return None


@app.on_event("startup")
def init():
    conn = db(); cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, name TEXT, price INT, stock INT)")
    for p in SEED:
        cur.execute("INSERT INTO products VALUES (%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING", p)
    conn.commit(); conn.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "catalog-api"}


@app.get("/products")
def list_products():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id,name,price,stock FROM products")
    rows = cur.fetchall(); conn.close()
    return {"products": [{"id": r[0], "name": r[1], "price": r[2], "stock": r[3]} for r in rows]}


@app.get("/products/{pid}")
def get_product(pid: str):
    # 1. Cache try (Redis) — fast path
    r = cache()
    if r:
        try:
            hit = r.get(f"product:{pid}")
            if hit:
                return {**json.loads(hit), "cached": True}
        except Exception:
            pass
    # 2. DB
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT id,name,price,stock FROM products WHERE id=%s", (pid,))
    row = cur.fetchone(); conn.close()
    if not row:
        raise HTTPException(404, "Product not found")
    data = {"id": row[0], "name": row[1], "price": row[2], "stock": row[3]}
    if r:
        try:
            r.setex(f"product:{pid}", 60, json.dumps(data))  # 60s cache
        except Exception:
            pass
    return {**data, "cached": False}
