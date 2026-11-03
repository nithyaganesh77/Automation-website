from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from app.schemas.document import DocumentOut
from app.schemas.invoice import InvoiceOut


class ApprovalHistoryOut(BaseModel):
    id: str
    reviewer_name: Optional[str] = "Reviewer"
    action: str  # APPROVE, REJECT, EDIT, REPROCESS
    comments: Optional[str] = None
    field_changes: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalRequestOut(BaseModel):
    id: str
    document_id: str
    invoice_id: Optional[str] = None
    status: str  # PENDING, APPROVED, REJECTED, REPROCESSING_REQUESTED
    priority: str
    created_at: datetime
    updated_at: datetime
    document: Optional[DocumentOut] = None
    invoice: Optional[InvoiceOut] = None
    history: List[ApprovalHistoryOut] = []

    class Config:
        from_attributes = True


class ApprovalActionRequest(BaseModel):
    action: Optional[str] = "APPROVE"  # APPROVE, REJECT, REPROCESS
    comments: Optional[str] = None
    notes: Optional[str] = None
    reason: Optional[str] = None
    field_changes: Optional[Dict[str, Any]] = None

