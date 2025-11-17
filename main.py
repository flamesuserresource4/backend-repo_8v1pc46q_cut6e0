import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Item, Vendor, Customer, Purchase, Sale, Payment, StockMovement

app = FastAPI(title="Hardware Shop ERP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class IdModel(BaseModel):
    id: str


def to_oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def coll(name: str):
    return db[name]


@app.get("/")
def read_root():
    return {"message": "Hardware Shop ERP Backend Running"}


@app.get("/schema")
def get_schema():
    # Return names so the DB viewer can introspect
    return {
        "collections": [
            "item", "vendor", "customer", "purchase", "sale", "payment", "stockmovement"
        ]
    }


# Master data CRUD: Items, Vendors, Customers
@app.post("/items")
def create_item(payload: Item):
    existing = coll("item").find_one({"sku": payload.sku})
    if existing:
        raise HTTPException(400, detail="SKU already exists")
    new_id = create_document("item", payload)
    return {"id": new_id}


@app.get("/items")
def list_items():
    return get_documents("item")


@app.post("/vendors")
def create_vendor(payload: Vendor):
    new_id = create_document("vendor", payload)
    return {"id": new_id}


@app.get("/vendors")
def list_vendors():
    return get_documents("vendor")


@app.post("/customers")
def create_customer(payload: Customer):
    new_id = create_document("customer", payload)
    return {"id": new_id}


@app.get("/customers")
def list_customers():
    return get_documents("customer")


# Purchases: create bill and stock-in movements
@app.post("/purchases")
def create_purchase(payload: Purchase):
    # Insert purchase document
    purchase_id = create_document("purchase", payload)

    # Create stock movements for each item (IN)
    for line in payload.items:
        movement = StockMovement(
            item_id=line.item_id,
            type="in",
            qty=line.qty,
            reason="purchase",
            ref_type="purchase",
            ref_id=purchase_id,
            date=datetime.utcnow(),
        )
        create_document("stockmovement", movement)
    return {"id": purchase_id}


@app.get("/purchases")
def list_purchases():
    return get_documents("purchase")


# Sales: create invoice and stock-out movements
@app.post("/sales")
def create_sale(payload: Sale):
    sale_id = create_document("sale", payload)
    for line in payload.items:
        movement = StockMovement(
            item_id=line.item_id,
            type="out",
            qty=line.qty,
            reason="sale",
            ref_type="sale",
            ref_id=sale_id,
            date=datetime.utcnow(),
        )
        create_document("stockmovement", movement)
    return {"id": sale_id}


@app.get("/sales")
def list_sales():
    return get_documents("sale")


# Payments
@app.post("/payments")
def create_payment(payload: Payment):
    payment_id = create_document("payment", payload)
    return {"id": payment_id}


@app.get("/payments")
def list_payments():
    return get_documents("payment")


# Stock report per item (current qty = openings + ins - outs)
@app.get("/stock")
def stock_report():
    items = list(coll("item").find({}))
    movements = list(coll("stockmovement").find({}))

    qty_map = {}
    for it in items:
        qty_map[str(it.get("_id"))] = float(it.get("opening_stock", 0))

    for m in movements:
        item_key = str(m.get("item_id")) if isinstance(m.get("item_id"), ObjectId) else m.get("item_id")
        if not item_key:
            continue
        qty_map[item_key] = qty_map.get(item_key, 0)
        if m.get("type") == "in":
            qty_map[item_key] += float(m.get("qty", 0))
        elif m.get("type") == "out":
            qty_map[item_key] -= float(m.get("qty", 0))

    report = []
    for it in items:
        key = str(it.get("_id"))
        report.append({
            "item_id": key,
            "name": it.get("name"),
            "sku": it.get("sku"),
            "on_hand": round(qty_map.get(key, 0), 2),
            "unit": it.get("unit", "pcs"),
        })
    return report


# Health check and DB test
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["collections"] = db.list_collection_names()
    except Exception as e:
        response["database"] = f"⚠️ {str(e)[:80]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
