"""Frontend — UI. Calls catalog-api + order-api (inter-service via service DNS)."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os
import httpx

app = FastAPI(title="frontend")

CATALOG_URL = os.environ.get("CATALOG_URL", "http://catalog-api:8000")
ORDER_URL = os.environ.get("ORDER_URL", "http://order-api:8000")


@app.get("/health")
def health():
    return {"status": "ok", "service": "frontend"}


@app.get("/", response_class=HTMLResponse)
def home():
    try:
        products = httpx.get(f"{CATALOG_URL}/products", timeout=5).json().get("products", [])
    except Exception:
        products = []
    rows = "".join(
        f"<tr><td>{p['name']}</td><td>₹{p['price']}</td><td>{p['stock']}</td></tr>"
        for p in products
    )
    return f"""
    <html><head><title>MicroShop</title></head>
    <body style="font-family:sans-serif;max-width:600px;margin:40px auto">
      <h1>🛒 MicroShop</h1>
      <p>Microservices demo — frontend → catalog-api + order-api</p>
      <table border="1" cellpadding="8">
        <tr><th>Product</th><th>Price</th><th>Stock</th></tr>
        {rows or '<tr><td colspan=3>catalog-api se products load nahi hue</td></tr>'}
      </table>
    </body></html>
    """
