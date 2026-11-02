from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class SupplierBase(BaseModel):
    name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"
    email: Optional[str] = None
    phone: Optional[str] = None


class SupplierCreateRequest(SupplierBase):
    pass


class SupplierUpdateRequest(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class SupplierOut(SupplierBase):
    id: str
    organization_id: str
    total_spend: Decimal
    invoice_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
