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
    primary_provider: str
    fallback_provider: str
    gemini_model: str
    groq_model: str
    gemini_configured: bool
    groq_configured: bool
    gemini_status: str
    groq_status: str
    disable_external_ai: bool
    daily_request_limit: int
    monthly_token_budget: int
    safe_quota_mode: bool
    confidence_threshold: float
    tax_tolerance: float
    currency: str


class SettingsUpdateRequest(BaseModel):
    primary_provider: Optional[str] = None
    fallback_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    groq_model: Optional[str] = None
    disable_external_ai: Optional[bool] = None
    daily_request_limit: Optional[int] = None
    monthly_token_budget: Optional[int] = None
    safe_quota_mode: Optional[bool] = None
    confidence_threshold: Optional[float] = None
    tax_tolerance: Optional[float] = None
    currency: Optional[str] = None


class TestConnectionRequest(BaseModel):
    provider: str  # "gemini" or "groq"
    api_key: Optional[str] = None


class TestConnectionResponse(BaseModel):
    success: bool
    message: str


class AIUsageTelemetryOut(BaseModel):
    gemini_requests: int
    gemini_tokens: int
    gemini_failures: int
    groq_requests: int
    groq_tokens: int
    groq_failures: int
    fallback_events: int
    estimated_cost_usd: float
    last_active_provider: str
    gemini_status: str
    groq_status: str
    primary_provider: str
    fallback_provider: str
    gemini_model: str
    groq_model: str
    privacy_mode: bool
    daily_request_limit: int
    monthly_token_budget: int
    safe_quota_mode: bool
