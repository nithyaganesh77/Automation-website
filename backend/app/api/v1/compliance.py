from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.models.all_models import (
    Organization, OrganizationSetting, DataRightsRequest, Document,
    Invoice, InvoiceLineItem, Supplier, AuditLog
)
from app.schemas.compliance import (
    ConsentWithdrawRequest, ConsentGrantRequest, ConsentStatusOut,
    TenantPrivacyPreferenceUpdate, TenantPrivacyPreferenceOut,
    DataExportRequest, DataExportSummaryOut, DataDeletionRequest,
    DataDeletionResponse, DataRightsRequestOut, RetentionPolicyOut,
    RetentionPolicyUpdate
)
from app.api.deps import AuthenticatedContext, get_current_user_context, require_roles
from app.core.config import settings as app_settings
from app.services.audit_service import AuditService

router = APIRouter(prefix="/compliance", tags=["Compliance & Data Rights"])


def _get_or_create_org_setting(db: Session, organization_id: str) -> OrganizationSetting:
    setting = db.query(OrganizationSetting).filter(
        OrganizationSetting.organization_id == organization_id
    ).first()
    if not setting:
        setting = OrganizationSetting(
            organization_id=organization_id,
            ai_provider="gemini",
            api_key_configured=bool(app_settings.GEMINI_API_KEY or app_settings.GROQ_API_KEY),
            confidence_threshold=0.85,
            tax_tolerance=2.00,
            auto_approve_threshold=0.98,
            currency="INR",
            tenant_disable_external_ai=False,
            consent_withdrawn=False,
            retention_policy_days=365
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.post("/consent/withdraw", response_model=ConsentStatusOut)
def withdraw_consent(
    req: ConsentWithdrawRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Super Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """
    Withdraw tenant customer consent for external AI processing (Google Gemini / Groq).
    Future uploads will strictly execute via deterministic local engines.
    Existing documents are preserved and NOT deleted.
    """
    setting = _get_or_create_org_setting(db, auth_ctx.organization_id)
    now = datetime.now(timezone.utc)

    setting.consent_withdrawn = True
    setting.consent_withdrawn_at = now
    db.commit()
    db.refresh(setting)

    # Log Data Rights Request
    dr_req = DataRightsRequest(
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        request_type="CONSENT_WITHDRAWAL",
        status="COMPLETED",
        details={"reason": req.reason, "timestamp": now.isoformat()},
        requested_at=now,
        completed_at=now,
        processed_by=auth_ctx.user.id,
        notes=req.reason or "Consent withdrawn by tenant administrator"
    )
    db.add(dr_req)

    # Immutable Audit Log
    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="CUSTOMER_CONSENT_WITHDRAWN",
        entity_type="ORGANIZATION_SETTING",
        entity_id=setting.id,
        details={
            "reason": req.reason,
            "effective_privacy_mode": True,
            "external_ai_prevented": True,
            "historical_documents_preserved": True
        }
    )

    effective_disabled = app_settings.DISABLE_EXTERNAL_AI or setting.tenant_disable_external_ai or setting.consent_withdrawn

    return ConsentStatusOut(
        organization_id=auth_ctx.organization_id,
        consent_withdrawn=True,
        consent_withdrawn_at=now,
        tenant_disable_external_ai=setting.tenant_disable_external_ai,
        global_privacy_mode_active=app_settings.DISABLE_EXTERNAL_AI,
        effective_external_ai_disabled=effective_disabled,
        message="Customer consent successfully withdrawn. External AI processing is disabled for all subsequent documents. Historical records are preserved."
    )


@router.post("/consent/grant", response_model=ConsentStatusOut)
def grant_consent(
    req: ConsentGrantRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Super Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """
    Re-grant customer consent for AI processing.
    Note: If global DISABLE_EXTERNAL_AI is True, external AI remains blocked.
    """
    setting = _get_or_create_org_setting(db, auth_ctx.organization_id)
    now = datetime.now(timezone.utc)

    setting.consent_withdrawn = False
    setting.consent_withdrawn_at = None
    db.commit()
    db.refresh(setting)

    dr_req = DataRightsRequest(
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        request_type="CONSENT_GRANTED",
        status="COMPLETED",
        details={"notes": req.notes, "timestamp": now.isoformat()},
        requested_at=now,
        completed_at=now,
        processed_by=auth_ctx.user.id,
        notes=req.notes or "Consent re-granted by tenant administrator"
    )
    db.add(dr_req)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="CUSTOMER_CONSENT_GRANTED",
        entity_type="ORGANIZATION_SETTING",
        entity_id=setting.id,
        details={"notes": req.notes}
    )

    effective_disabled = app_settings.DISABLE_EXTERNAL_AI or setting.tenant_disable_external_ai or setting.consent_withdrawn

    return ConsentStatusOut(
        organization_id=auth_ctx.organization_id,
        consent_withdrawn=False,
        consent_withdrawn_at=None,
        tenant_disable_external_ai=setting.tenant_disable_external_ai,
        global_privacy_mode_active=app_settings.DISABLE_EXTERNAL_AI,
        effective_external_ai_disabled=effective_disabled,
        message="Customer consent granted." + (" (Note: Global air-gap privacy mode remains active on host)" if app_settings.DISABLE_EXTERNAL_AI else "")
    )


@router.get("/consent/status", response_model=ConsentStatusOut)
def get_consent_status(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """View tenant-specific consent and external AI processing status."""
    setting = _get_or_create_org_setting(db, auth_ctx.organization_id)
    effective_disabled = app_settings.DISABLE_EXTERNAL_AI or setting.tenant_disable_external_ai or setting.consent_withdrawn

    return ConsentStatusOut(
        organization_id=auth_ctx.organization_id,
        consent_withdrawn=setting.consent_withdrawn,
        consent_withdrawn_at=setting.consent_withdrawn_at,
        tenant_disable_external_ai=setting.tenant_disable_external_ai,
        global_privacy_mode_active=app_settings.DISABLE_EXTERNAL_AI,
        effective_external_ai_disabled=effective_disabled,
        message="Active" if not effective_disabled else "External AI is disabled"
    )


@router.get("/preferences", response_model=TenantPrivacyPreferenceOut)
def get_tenant_privacy_preferences(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """Inspect tenant-specific external AI processing preferences."""
    setting = _get_or_create_org_setting(db, auth_ctx.organization_id)
    effective_disabled = app_settings.DISABLE_EXTERNAL_AI or setting.tenant_disable_external_ai or setting.consent_withdrawn

    return TenantPrivacyPreferenceOut(
        organization_id=auth_ctx.organization_id,
        tenant_disable_external_ai=setting.tenant_disable_external_ai,
        consent_withdrawn=setting.consent_withdrawn,
        global_privacy_mode_active=app_settings.DISABLE_EXTERNAL_AI,
        effective_external_ai_disabled=effective_disabled,
        data_rights_contact_email=setting.data_rights_contact_email
    )


@router.patch("/preferences", response_model=TenantPrivacyPreferenceOut)
def update_tenant_privacy_preferences(
    req: TenantPrivacyPreferenceUpdate,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Super Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """
    Update tenant privacy preferences.
    Security guarantee: Global privacy mode (DISABLE_EXTERNAL_AI=True) CANNOT be bypassed.
    """
    setting = _get_or_create_org_setting(db, auth_ctx.organization_id)

    if req.tenant_disable_external_ai is not None:
        setting.tenant_disable_external_ai = req.tenant_disable_external_ai
    if req.data_rights_contact_email is not None:
        setting.data_rights_contact_email = req.data_rights_contact_email

    db.commit()
    db.refresh(setting)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="TENANT_PRIVACY_PREFERENCES_UPDATED",
        entity_type="ORGANIZATION_SETTING",
        entity_id=setting.id,
        details={
            "tenant_disable_external_ai": setting.tenant_disable_external_ai,
            "data_rights_contact_email": setting.data_rights_contact_email
        }
    )

    effective_disabled = app_settings.DISABLE_EXTERNAL_AI or setting.tenant_disable_external_ai or setting.consent_withdrawn

    return TenantPrivacyPreferenceOut(
        organization_id=auth_ctx.organization_id,
        tenant_disable_external_ai=setting.tenant_disable_external_ai,
        consent_withdrawn=setting.consent_withdrawn,
        global_privacy_mode_active=app_settings.DISABLE_EXTERNAL_AI,
        effective_external_ai_disabled=effective_disabled,
        data_rights_contact_email=setting.data_rights_contact_email
    )


@router.post("/export", response_model=DataExportSummaryOut)
def request_data_export(
    req: DataExportRequest,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """
    Export all tenant-isolated data for GDPR/DPDP data portability compliance.
    """
    now = datetime.now(timezone.utc)
    org_id = auth_ctx.organization_id

    # Tenant-isolated records
    invoices = db.query(Invoice).filter(Invoice.organization_id == org_id).all()
    documents = db.query(Document).filter(Document.organization_id == org_id).all()
    suppliers = db.query(Supplier).filter(Supplier.organization_id == org_id).all()
    audit_logs = db.query(AuditLog).filter(AuditLog.organization_id == org_id).order_by(desc(AuditLog.created_at)).limit(500).all()

    export_payload = {
        "export_metadata": {
            "organization_id": org_id,
            "exported_at": now.isoformat(),
            "exported_by_user_id": auth_ctx.user.id,
            "export_type": req.export_type
        },
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date,
                "supplier_name": inv.supplier_name_raw,
                "supplier_gstin": inv.supplier_gstin_raw,
                "subtotal": float(inv.subtotal),
                "tax_amount": float(inv.total_tax),
                "grand_total": float(inv.grand_total),
                "status": inv.status,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "line_items": [
                    {
                        "line_number": li.line_number,
                        "description": li.description,
                        "quantity": float(li.quantity),
                        "unit_price": float(li.unit_price),
                        "line_total": float(li.line_total)
                    }
                    for li in inv.line_items
                ]
            }
            for inv in invoices
        ],
        "documents": [
            {
                "id": d.id,
                "file_name": d.file_name,
                "file_size": d.file_size,
                "mime_type": d.mime_type,
                "file_hash_sha256": d.file_hash_sha256,
                "status": d.status,
                "document_type": d.document_type,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in documents
        ],
        "suppliers": [
            {
                "id": s.id,
                "name": s.name,
                "gstin": s.gstin,
                "total_spend": float(s.total_spend),
                "invoice_count": s.invoice_count
            }
            for s in suppliers
        ],
        "audit_logs": [
            {
                "id": a.id,
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "timestamp": a.created_at.isoformat() if a.created_at else None,
                "details": a.details
            }
            for a in audit_logs
        ]
    }

    # Register Data Rights Request
    dr_req = DataRightsRequest(
        organization_id=org_id,
        user_id=auth_ctx.user.id,
        request_type="DATA_EXPORT",
        status="COMPLETED",
        details={
            "export_type": req.export_type,
            "format": req.format,
            "counts": {
                "invoices": len(invoices),
                "documents": len(documents),
                "suppliers": len(suppliers),
                "audit_logs": len(audit_logs)
            }
        },
        requested_at=now,
        completed_at=now,
        processed_by=auth_ctx.user.id,
        notes="Export generated successfully."
    )
    db.add(dr_req)
    db.commit()
    db.refresh(dr_req)

    AuditService.log_event(
        db=db,
        organization_id=org_id,
        user_id=auth_ctx.user.id,
        action="DATA_EXPORT_GENERATED",
        entity_type="DATA_EXPORT",
        entity_id=dr_req.id,
        details={"record_count": len(invoices) + len(documents)}
    )

    return DataExportSummaryOut(
        request_id=dr_req.id,
        organization_id=org_id,
        export_type=req.export_type,
        format=req.format,
        total_documents=len(documents),
        total_invoices=len(invoices),
        total_suppliers=len(suppliers),
        total_audit_logs=len(audit_logs),
        generated_at=now,
        data=export_payload
    )


@router.post("/deletion-request", response_model=DataRightsRequestOut)
def request_data_deletion(
    req: DataDeletionRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Super Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """
    Register a data deletion (right to be forgotten) request.
    Requires explicit confirmation phrase: 'DELETE ALL TENANT DATA'.
    """
    if req.confirm_phrase != "DELETE ALL TENANT DATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation phrase mismatch. Please provide exact phrase 'DELETE ALL TENANT DATA'."
        )

    now = datetime.now(timezone.utc)
    dr_req = DataRightsRequest(
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        request_type="DATA_DELETION",
        status="PENDING",
        details={"reason": req.reason, "requested_at": now.isoformat()},
        requested_at=now,
        notes=f"Deletion requested by {auth_ctx.user.email}. Reason: {req.reason}"
    )
    db.add(dr_req)
    db.commit()
    db.refresh(dr_req)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="DATA_DELETION_REQUESTED",
        entity_type="DATA_RIGHTS_REQUEST",
        entity_id=dr_req.id,
        details={"reason": req.reason}
    )

    return dr_req


@router.post("/deletion-request/{request_id}/execute", response_model=DataDeletionResponse)
def execute_data_deletion(
    request_id: str,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Super Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """
    Execute an approved tenant data deletion request.
    Strict tenant boundary: Deletes all tenant documents, invoices, line items, and suppliers.
    Preserves user credentials and registers final immutable deletion audit record.
    """
    dr_req = db.query(DataRightsRequest).filter(
        DataRightsRequest.id == request_id,
        DataRightsRequest.organization_id == auth_ctx.organization_id
    ).first()

    if not dr_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data deletion request not found.")

    if dr_req.status == "COMPLETED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deletion request already executed.")

    org_id = auth_ctx.organization_id

    # Perform cascading tenant-isolated deletions
    inv_count = db.query(Invoice).filter(Invoice.organization_id == org_id).delete(synchronize_session=False)
    doc_count = db.query(Document).filter(Document.organization_id == org_id).delete(synchronize_session=False)
    sup_count = db.query(Supplier).filter(Supplier.organization_id == org_id).delete(synchronize_session=False)

    now = datetime.now(timezone.utc)
    dr_req.status = "COMPLETED"
    dr_req.completed_at = now
    dr_req.processed_by = auth_ctx.user.id
    dr_req.details = {
        **dr_req.details,
        "purged_records": {
            "invoices": inv_count,
            "documents": doc_count,
            "suppliers": sup_count
        }
    }
    db.commit()

    # Final immutable audit log entry
    AuditService.log_event(
        db=db,
        organization_id=org_id,
        user_id=auth_ctx.user.id,
        action="TENANT_DATA_PURGED_UNDER_DATA_RIGHTS",
        entity_type="DATA_RIGHTS_REQUEST",
        entity_id=request_id,
        details={
            "invoices_purged": inv_count,
            "documents_purged": doc_count,
            "suppliers_purged": sup_count,
            "executed_by": auth_ctx.user.email
        }
    )

    return DataDeletionResponse(
        request_id=request_id,
        organization_id=org_id,
        status="COMPLETED",
        records_purged={"invoices": inv_count, "documents": doc_count, "suppliers": sup_count},
        completed_at=now,
        message="Tenant document, invoice, and supplier records successfully purged in accordance with customer data rights."
    )


@router.get("/retention-policy", response_model=RetentionPolicyOut)
def get_retention_policy(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """View tenant data retention policy and auto-purge status."""
    setting = _get_or_create_org_setting(db, auth_ctx.organization_id)
    days = setting.retention_policy_days or 365

    return RetentionPolicyOut(
        organization_id=auth_ctx.organization_id,
        retention_policy_days=days,
        effective_policy_text=f"Processed invoices and source documents are retained for {days} days from ingestion before eligibility for automated archival/purge.",
        auto_purge_eligible=True
    )


@router.patch("/retention-policy", response_model=RetentionPolicyOut)
def update_retention_policy(
    req: RetentionPolicyUpdate,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Super Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """Update organization data retention policy period (30 to 3650 days)."""
    if req.retention_policy_days < 30 or req.retention_policy_days > 3650:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retention period must be between 30 and 3650 days (10 years)."
        )

    setting = _get_or_create_org_setting(db, auth_ctx.organization_id)
    setting.retention_policy_days = req.retention_policy_days
    db.commit()
    db.refresh(setting)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="RETENTION_POLICY_UPDATED",
        entity_type="ORGANIZATION_SETTING",
        entity_id=setting.id,
        details={"new_retention_days": req.retention_policy_days}
    )

    return RetentionPolicyOut(
        organization_id=auth_ctx.organization_id,
        retention_policy_days=setting.retention_policy_days,
        effective_policy_text=f"Processed invoices and source documents are retained for {setting.retention_policy_days} days from ingestion before eligibility for automated archival/purge.",
        auto_purge_eligible=True
    )


@router.get("/requests", response_model=List[DataRightsRequestOut])
def list_compliance_requests(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """List data rights and compliance requests for the tenant."""
    requests = db.query(DataRightsRequest).filter(
        DataRightsRequest.organization_id == auth_ctx.organization_id
    ).order_by(desc(DataRightsRequest.requested_at)).limit(limit).all()
    return requests

