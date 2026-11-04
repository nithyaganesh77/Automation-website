from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConsentWithdrawRequest(BaseModel):
    reason: Optional[str] = None


class ConsentGrantRequest(BaseModel):
    notes: Optional[str] = None


class ConsentStatusOut(BaseModel):
    organization_id: str
    consent_withdrawn: bool
    consent_withdrawn_at: Optional[datetime] = None
    tenant_disable_external_ai: bool
    global_privacy_mode_active: bool
    effective_external_ai_disabled: bool
    message: str


class TenantPrivacyPreferenceUpdate(BaseModel):
    tenant_disable_external_ai: Optional[bool] = None
    data_rights_contact_email: Optional[str] = None


class TenantPrivacyPreferenceOut(BaseModel):
    organization_id: str
    tenant_disable_external_ai: bool
    consent_withdrawn: bool
    global_privacy_mode_active: bool
    effective_external_ai_disabled: bool
    data_rights_contact_email: Optional[str] = None


class DataExportRequest(BaseModel):
    export_type: str = "ALL"  # ALL, INVOICES, DOCUMENTS, AUDIT_LOGS
    format: str = "JSON"  # JSON


class DataExportSummaryOut(BaseModel):
    request_id: str
    organization_id: str
    export_type: str
    format: str
    total_documents: int
    total_invoices: int
    total_suppliers: int
    total_audit_logs: int
    generated_at: datetime
    data: Optional[Dict[str, Any]] = None


class DataDeletionRequest(BaseModel):
    reason: str
    confirm_phrase: str  # Must match "DELETE ALL TENANT DATA"


class DataDeletionResponse(BaseModel):
    request_id: str
    organization_id: str
    status: str
    records_purged: Dict[str, int]
    completed_at: datetime
    message: str


class DataRightsRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    user_id: str
    request_type: str
    status: str
    details: Dict[str, Any]
    requested_at: datetime
    completed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    notes: Optional[str] = None


class RetentionPolicyOut(BaseModel):
    organization_id: str
    retention_policy_days: int
    effective_policy_text: str
    auto_purge_eligible: bool


class RetentionPolicyUpdate(BaseModel):
    retention_policy_days: int

