"""
ERP Database Schemas for Hardware Shop

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercase of the class name (e.g., Item -> "item").

These schemas are used for request validation and for documenting your data
model. Fields are chosen to cover common hardware shop ERP needs: catalog,
parties (vendors/customers), purchases, sales, stock movements and payments.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Item(BaseModel):
    name: str = Field(..., description="Item/Product name")
    sku: str = Field(..., description="Stock keeping unit (unique code)")
    category: Optional[str] = Field(None, description="Category name")
    unit: str = Field("pcs", description="Unit of measure (pcs, box, kg, etc.)")
    tax_rate: float = Field(0.0, ge=0, le=100, description="Tax/VAT percentage")
    cost_price: float = Field(0.0, ge=0, description="Default cost price")
    sale_price: float = Field(0.0, ge=0, description="Default selling price")
    reorder_level: int = Field(0, ge=0, description="Reorder threshold")
    opening_stock: float = Field(0, ge=0, description="Opening quantity on hand")
    barcode: Optional[str] = Field(None, description="Barcode if available")
    is_active: bool = Field(True)


class Vendor(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = Field(None, description="Tax registration number if applicable")
    notes: Optional[str] = None
    is_active: bool = True


class Customer(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class PurchaseItem(BaseModel):
    item_id: str = Field(..., description="Item ObjectId as string")
    qty: float = Field(..., gt=0)
    cost: float = Field(..., ge=0)
    tax_rate: float = Field(0.0, ge=0, le=100)
    discount: float = Field(0.0, ge=0, description="Flat discount per line")


class Purchase(BaseModel):
    vendor_id: str
    bill_number: Optional[str] = None
    bill_date: Optional[datetime] = None
    items: List[PurchaseItem]
    other_charges: float = 0.0
    notes: Optional[str] = None
    payment_status: str = Field("unpaid", description="unpaid, partial, paid")


class SaleItem(BaseModel):
    item_id: str
    qty: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    discount: float = Field(0.0, ge=0)
    tax_rate: float = Field(0.0, ge=0, le=100)


class Sale(BaseModel):
    customer_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    items: List[SaleItem]
    other_charges: float = 0.0
    notes: Optional[str] = None
    payment_status: str = Field("unpaid", description="unpaid, partial, paid")


class Payment(BaseModel):
    ref_type: str = Field(..., description="purchase or sale")
    ref_id: str = Field(..., description="Reference document id")
    amount: float = Field(..., gt=0)
    method: str = Field("cash", description="cash, card, upi, bank, etc.")
    date: Optional[datetime] = None
    notes: Optional[str] = None


class StockMovement(BaseModel):
    item_id: str
    type: str = Field(..., description="in or out")
    qty: float = Field(..., gt=0)
    reason: str = Field(..., description="purchase, sale, opening, adjust, return")
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    date: Optional[datetime] = None
