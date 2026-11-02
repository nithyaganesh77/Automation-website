from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.session import get_db
from app.models.all_models import ApprovalRequest, ApprovalHistory, Document, Invoice, Supplier
from app.schemas.approval import ApprovalRequestOut, ApprovalActionRequest
from app.api.deps import AuthenticatedContext, get_current_user_context, require_roles
from app.services.audit_service import AuditService

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("", response_model=List[ApprovalRequestOut])
def get_approval_requests(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db),
    status: Optional[str] = Query("PENDING")
):
    query = db.query(ApprovalRequest).filter(ApprovalRequest.organization_id == auth_ctx.organization_id)
    if status and status != "ALL":
        query = query.filter(ApprovalRequest.status == status)

    requests = query.order_by(desc(ApprovalRequest.created_at)).all()
    return requests


@router.post("/{approval_id}/approve", response_model=ApprovalRequestOut)
def approve_request(
    approval_id: str,
    action_data: ApprovalActionRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Reviewer"])),
    db: Session = Depends(get_db)
):
    req = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id,
        ApprovalRequest.organization_id == auth_ctx.organization_id
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    req.status = "APPROVED"

    # Mark document as APPROVED
    doc = db.query(Document).filter(Document.id == req.document_id).first()
    if doc:
        doc.status = "APPROVED"

    # Mark invoice as APPROVED & update supplier statistics
    inv = db.query(Invoice).filter(Invoice.document_id == req.document_id).first()
    if inv:
        inv.status = "APPROVED"
        if inv.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == inv.supplier_id).first()
            if supplier:
                supplier.total_spend += inv.grand_total
                supplier.invoice_count += 1

    # Record approval history
    history = ApprovalHistory(
        approval_request_id=req.id,
        reviewer_id=auth_ctx.user.id,
        action="APPROVE",
        comments=action_data.comments or "Approved by reviewer",
        field_changes=action_data.field_changes or {}
    )
    db.add(history)
    db.commit()

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="DOCUMENT_APPROVED",
        entity_type="APPROVAL_REQUEST",
        entity_id=req.id,
        details={"comments": action_data.comments, "invoice_id": inv.id if inv else None}
    )

    db.refresh(req)
    return req


@router.post("/{approval_id}/reject", response_model=ApprovalRequestOut)
def reject_request(
    approval_id: str,
    action_data: ApprovalActionRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Reviewer"])),
    db: Session = Depends(get_db)
):
    req = db.query(ApprovalRequest).filter(
        ApprovalRequest.id == approval_id,
        ApprovalRequest.organization_id == auth_ctx.organization_id
    ).first()

    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    req.status = "REJECTED"

    doc = db.query(Document).filter(Document.id == req.document_id).first()
    if doc:
        doc.status = "REJECTED"

    inv = db.query(Invoice).filter(Invoice.document_id == req.document_id).first()
    if inv:
        inv.status = "REJECTED"

    history = ApprovalHistory(
        approval_request_id=req.id,
        reviewer_id=auth_ctx.user.id,
        action="REJECT",
        comments=action_data.comments or "Rejected by reviewer",
        field_changes=action_data.field_changes or {}
    )
    db.add(history)
    db.commit()

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="DOCUMENT_REJECTED",
        entity_type="APPROVAL_REQUEST",
        entity_id=req.id,
        details={"comments": action_data.comments}
    )

    db.refresh(req)
    return req
