from pydantic import BaseModel, Field
import os
import time
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://shop:shop123@db:5432/products"
)

SEED_PRODUCTS = [
    ("Cotton Kurta", "Clothing", 2500, 40),
    ("Denim Jeans", "Clothing", 3200, 25),
    ("Wireless Earbuds", "Electronics", 4500, 60),
    ("Bluetooth Speaker", "Electronics", 6800, 15),
    ("Smart Watch", "Electronics", 9500, 10),
    ("Leather Wallet", "Accessories", 1800, 50),
]


def get_conn():
    return psycopg.connect(DATABASE_URL)


def init_db():
    # Database kabhi kabhi der se ready hoti hai, isliye kuch baar dobara try karte hain
    for attempt in range(10):
        try:
            with get_conn() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        price INTEGER NOT NULL,
                        stock INTEGER NOT NULL
                    )
                    """
                )
                count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                if count == 0:
                    for p in SEED_PRODUCTS:
                        conn.execute(
                            "INSERT INTO products (name, category, price, stock) "
                            "VALUES (%s, %s, %s, %s)",
                            p,
                        )
            return
        except psycopg.OperationalError:
            print(f"Database ready nahi, dobara try ({attempt + 1}/10)")
            time.sleep(2)
    raise RuntimeError("Database se connect nahi ho saka")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Products Service", lifespan=lifespan)


def row_to_dict(row):
    return {
        "id": row[0],
        "name": row[1],
        "category": row[2],
        "price": row[3],
        "stock": row[4],
    }


@app.get("/")
def root():
    return {"service": "products", "version": "0.3"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products")
def list_products():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, category, price, stock FROM products ORDER BY id"
        ).fetchall()
    return [row_to_dict(r) for r in rows]


@app.get("/products/{product_id}")
def get_product(product_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, category, price, stock FROM products WHERE id = %s",
            (product_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product nahi mila")
    return row_to_dict(row)


@app.get("/ready")
def ready():
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database ready nahi")
    return {"status": "ready"}


class Reservation(BaseModel):
    quantity: int = Field(ge=1, le=20)


@app.post("/products/{product_id}/reserve")
def reserve(product_id: int, body: Reservation):
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE products SET stock = stock - %s "
            "WHERE id = %s AND stock >= %s "
            "RETURNING id, name, category, price, stock",
            (body.quantity, product_id, body.quantity),
        ).fetchone()

    if row is None:
        with get_conn() as conn:
            exists = conn.execute(
                "SELECT 1 FROM products WHERE id = %s", (product_id,)
            ).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Product nahi mila")
        raise HTTPException(status_code=409, detail="Stock kam hai")

    return row_to_dict(row)


@app.post("/products/{product_id}/release")
def release(product_id: int, body: Reservation):
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE products SET stock = stock + %s WHERE id = %s "
            "RETURNING id, name, category, price, stock",
            (body.quantity, product_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product nahi mila")
    return row_to_dict(row)
