from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class DashboardMetricsOut(BaseModel):
    total_documents: int
    total_invoices: int
    processed_documents: int
    pending_approvals: int
    failed_documents: int
    duplicate_warnings: int
    total_invoice_value: Decimal
    currency: str = "INR"
    monthly_expense_trend: List[Dict[str, Any]]
    processing_status_distribution: List[Dict[str, Any]]
    document_type_distribution: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


class ExpenseTrendItem(BaseModel):
    month: str
    total_amount: Decimal
    tax_amount: Decimal
    invoice_count: int


class SupplierSpendItem(BaseModel):
    supplier_id: str
    supplier_name: str
    total_spend: Decimal
    invoice_count: int
    percentage_of_total: float


class ExportRequest(BaseModel):
    export_type: str = "INVOICES"  # INVOICES, EXPENSES, TAX_SUMMARY, SUPPLIERS
    format: str = "EXCEL"  # EXCEL, CSV, PDF, JSON
    filters: Optional[Dict[str, Any]] = None


class ExportRecordOut(BaseModel):
    id: str
    export_type: str
    format: str
    record_count: int
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class SettingsOut(BaseModel):
    ai_provider: str
    api_key_configured: bool
    confidence_threshold: float
    tax_tolerance: float
    auto_approve_threshold: float
    currency: str


class SettingsUpdateRequest(BaseModel):
    ai_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    confidence_threshold: Optional[float] = None
    tax_tolerance: Optional[float] = None
    auto_approve_threshold: Optional[float] = None
    currency: Optional[str] = None
