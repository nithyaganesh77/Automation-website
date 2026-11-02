from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from app.schemas.invoice import InvoiceOut
from app.schemas.validation import ValidationResultOut


class DocumentPageOut(BaseModel):
    id: str
    page_number: int
    extracted_text: str
    ocr_engine: str
    confidence: float
    page_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ExtractedFieldOut(BaseModel):
    id: str
    field_name: str
    field_value: Optional[str] = None
    confidence: float
    source_page: int
    evidence_text: Optional[str] = None
    is_corrected: bool

    class Config:
        from_attributes = True


class DuplicateMatchOut(BaseModel):
    id: str
    matched_document_id: str
    match_type: str
    match_score: float
    match_details: Dict[str, Any]
    is_confirmed: bool

    class Config:
        from_attributes = True


class AnomalyFindingOut(BaseModel):
    id: str
    anomaly_type: str
    severity: str
    description: str
    details: Dict[str, Any]

    class Config:
        from_attributes = True


class AgentExecutionOut(BaseModel):
    id: str
    agent_name: str
    status: str
    latency_ms: int
    tokens_used: int
    cost_usd: float
    created_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: str
    organization_id: str
    file_name: str
    file_size: int
    mime_type: str
    status: str
    document_type: str
    confidence: float
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    grand_total: Optional[float] = None

    class Config:
        from_attributes = True


class DocumentDetailOut(DocumentOut):
    file_path: str
    pages: List[DocumentPageOut] = []
    extracted_fields: List[ExtractedFieldOut] = []
    invoice: Optional[InvoiceOut] = None
    validations: List[ValidationResultOut] = []
    duplicates: List[DuplicateMatchOut] = []
    anomalies: List[AnomalyFindingOut] = []
    agent_executions: List[AgentExecutionOut] = []

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: List[DocumentOut]
    total: int
    page: int
    page_size: int
    total_pages: int

