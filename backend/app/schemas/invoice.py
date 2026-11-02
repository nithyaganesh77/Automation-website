from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


class InvoiceLineItemBase(BaseModel):
    line_number: int = 1
    description: str
    hsn_sac: Optional[str] = None
    quantity: Decimal = Decimal("1.000")
    unit: Optional[str] = "Nos"
    unit_price: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    line_total: Decimal = Decimal("0.00")


class InvoiceLineItemCreate(InvoiceLineItemBase):
    pass


class InvoiceLineItemOut(InvoiceLineItemBase):
    id: str
    invoice_id: str

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    invoice_number: str
    invoice_date: str
    due_date: Optional[str] = None
    supplier_name_raw: Optional[str] = None
    supplier_gstin_raw: Optional[str] = None
    supplier_address_raw: Optional[str] = None
    customer_name_raw: Optional[str] = None
    customer_gstin_raw: Optional[str] = None
    customer_address_raw: Optional[str] = None
    currency: str = "INR"
    subtotal: Decimal = Decimal("0.00")
    taxable_amount: Decimal = Decimal("0.00")
    cgst: Decimal = Decimal("0.00")
    sgst: Decimal = Decimal("0.00")
    igst: Decimal = Decimal("0.00")
    total_tax: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    other_charges: Decimal = Decimal("0.00")
    grand_total: Decimal = Decimal("0.00")
    payment_terms: Optional[str] = None
    purchase_order_number: Optional[str] = None


class InvoiceUpdateRequest(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    supplier_name_raw: Optional[str] = None
    supplier_gstin_raw: Optional[str] = None
    supplier_address_raw: Optional[str] = None
    customer_name_raw: Optional[str] = None
    customer_gstin_raw: Optional[str] = None
    customer_address_raw: Optional[str] = None
    currency: Optional[str] = None
    subtotal: Optional[Decimal] = None
    taxable_amount: Optional[Decimal] = None
    cgst: Optional[Decimal] = None
    sgst: Optional[Decimal] = None
    igst: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    other_charges: Optional[Decimal] = None
    grand_total: Optional[Decimal] = None
    payment_terms: Optional[str] = None
    purchase_order_number: Optional[str] = None
    line_items: Optional[List[InvoiceLineItemBase]] = None


class InvoiceOut(InvoiceBase):
    id: str
    document_id: str
    organization_id: str
    supplier_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: str
    line_items: List[InvoiceLineItemOut] = []

    class Config:
        from_attributes = True

