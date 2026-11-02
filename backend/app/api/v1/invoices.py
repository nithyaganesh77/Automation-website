from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.session import get_db
from app.models.all_models import Invoice, InvoiceLineItem, ValidationResult, ExtractedField
from app.schemas.invoice import InvoiceOut, InvoiceUpdateRequest
from app.schemas.validation import ValidationResultOut
from app.api.deps import AuthenticatedContext, get_current_user_context
from app.services.validation_engine import ValidationEngine
from app.services.audit_service import AuditService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("", response_model=List[InvoiceOut])
def get_invoices(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    query = db.query(Invoice).filter(Invoice.organization_id == auth_ctx.organization_id)
    if status:
        query = query.filter(Invoice.status == status)
    if supplier:
        query = query.filter(Invoice.supplier_name_raw.ilike(f"%{supplier}%"))

    return query.order_by(desc(Invoice.created_at)).limit(limit).all()


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice_by_id(
    invoice_id: str,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.organization_id == auth_ctx.organization_id
    ).first()

    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: str,
    update_data: InvoiceUpdateRequest,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.organization_id == auth_ctx.organization_id
    ).first()

    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    changes = {}
    for field, val in update_data.model_dump(exclude_unset=True).items():
        if field == "line_items":
            continue
        if val is not None:
            old_val = getattr(inv, field)
            setattr(inv, field, val)
            changes[field] = {"old": str(old_val), "new": str(val)}

    # Update line items if provided
    if update_data.line_items is not None:
        db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == inv.id).delete()
        for idx, li in enumerate(update_data.line_items):
            item = InvoiceLineItem(
                invoice_id=inv.id,
                line_number=li.line_number or (idx + 1),
                description=li.description,
                hsn_sac=li.hsn_sac,
                quantity=li.quantity,
                unit=li.unit,
                unit_price=li.unit_price,
                discount=li.discount,
                tax_rate=li.tax_rate,
                tax_amount=li.tax_amount,
                line_total=li.line_total
            )
            db.add(item)
        changes["line_items_updated"] = True

    db.commit()

    # Re-run validation on updated values
    val_status, is_valid, errors, warnings, explanations = ValidationEngine.validate_invoice({
        "invoice_number": inv.invoice_number,
        "invoice_date": inv.invoice_date,
        "due_date": inv.due_date,
        "supplier_name": inv.supplier_name_raw,
        "supplier_gstin": inv.supplier_gstin_raw,
        "subtotal": inv.subtotal,
        "taxable_amount": inv.taxable_amount,
        "cgst": inv.cgst,
        "sgst": inv.sgst,
        "igst": inv.igst,
        "total_tax": inv.total_tax,
        "discount": inv.discount,
        "other_charges": inv.other_charges,
        "grand_total": inv.grand_total,
        "line_items": [
            {
                "quantity": float(li.quantity),
                "unit_price": float(li.unit_price),
                "discount": float(li.discount),
                "tax_amount": float(li.tax_amount),
                "line_total": float(li.line_total)
            }
            for li in inv.line_items
        ]
    })

    # Update validation result record
    val_rec = db.query(ValidationResult).filter(ValidationResult.invoice_id == inv.id).first()
    if val_rec:
        val_rec.status = val_status
        val_rec.is_valid = is_valid
        val_rec.errors = errors
        val_rec.warnings = warnings
        val_rec.field_explanations = explanations
        db.commit()

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="INVOICE_EDITED",
        entity_type="INVOICE",
        entity_id=inv.id,
        details={"changes": changes}
    )

    db.refresh(inv)
    return inv


@router.get("/{invoice_id}/validation", response_model=ValidationResultOut)
def get_invoice_validation(
    invoice_id: str,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.organization_id == auth_ctx.organization_id
    ).first()

    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    val = db.query(ValidationResult).filter(ValidationResult.document_id == inv.document_id).first()
    if not val:
        raise HTTPException(status_code=404, detail="Validation result not found")
    return val
