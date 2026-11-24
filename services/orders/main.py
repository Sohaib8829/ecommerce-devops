import os

import httpx
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
PRODUCTS_URL = os.getenv("PRODUCTS_URL", "http://products:8000")
CART_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 din

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="Orders Service")


class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)


def cart_key(user_id: str) -> str:
    return f"cart:{user_id}"


def fetch_product(product_id: int) -> dict:
    try:
        resp = httpx.get(f"{PRODUCTS_URL}/products/{product_id}", timeout=3.0)
    except httpx.RequestError:
        raise HTTPException(
            status_code=503, detail="Products service tak pahunch nahi saka"
        )
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Product nahi mila")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502, detail="Products service ne ghalat jawab diya"
        )
    return resp.json()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        r.ping()
    except redis.RedisError:
        raise HTTPException(status_code=503, detail="Redis ready nahi")
    return {"status": "ready"}


@app.get("/cart/{user_id}")
def get_cart(user_id: str):
    data = r.hgetall(cart_key(user_id))
    items = [
        {"product_id": int(field.split(":")[1]), "quantity": int(qty)}
        for field, qty in data.items()
    ]
    return {"user_id": user_id, "items": items, "ttl_seconds": r.ttl(cart_key(user_id))}


@app.post("/cart/{user_id}/items")
def add_item(user_id: str, item: CartItem):
    product = fetch_product(item.product_id)

    key = cart_key(user_id)
    field = f"product:{item.product_id}"
    already = int(r.hget(key, field) or 0)
    if already + item.quantity > product["stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"Stock kam hai, sirf {product['stock']} maujood hain",
        )

    r.hincrby(key, field, item.quantity)
    r.expire(key, CART_TTL_SECONDS)
    return get_cart(user_id)


@app.delete("/cart/{user_id}")
def clear_cart(user_id: str):
    r.delete(cart_key(user_id))
    return {"status": "cleared"}
