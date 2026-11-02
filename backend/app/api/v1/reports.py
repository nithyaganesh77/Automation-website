import os
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.session import get_db
from app.models.all_models import (
    Document, Invoice, DuplicateMatch, ValidationResult, Supplier, ExportRecord, AuditLog
)
from app.schemas.report import (
    DashboardMetricsOut, ExpenseTrendItem, SupplierSpendItem, ExportRequest, ExportRecordOut
)
from app.api.deps import AuthenticatedContext, get_current_user_context
from app.services.export_engine import ExportEngine
from app.services.audit_service import AuditService

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("/dashboard", response_model=DashboardMetricsOut)
def get_dashboard_metrics(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    org_id = auth_ctx.organization_id

    # 1. High-level KPI Counts
    total_docs = db.query(func.count(Document.id)).filter(Document.organization_id == org_id).scalar() or 0
    total_invoices = db.query(func.count(Invoice.id)).filter(Invoice.organization_id == org_id).scalar() or 0
    processed_docs = db.query(func.count(Document.id)).filter(
        Document.organization_id == org_id,
        Document.status.in_(["APPROVED", "COMPLETED", "NEEDS_REVIEW"])
    ).scalar() or 0
    pending_approvals = db.query(func.count(Document.id)).filter(
        Document.organization_id == org_id,
        Document.status == "NEEDS_REVIEW"
    ).scalar() or 0
    failed_docs = db.query(func.count(Document.id)).filter(
        Document.organization_id == org_id,
        Document.status == "FAILED"
    ).scalar() or 0

    duplicate_warnings = db.query(func.count(DuplicateMatch.id)).join(Document, DuplicateMatch.document_id == Document.id).filter(
        Document.organization_id == org_id
    ).scalar() or 0

    total_val = db.query(func.sum(Invoice.grand_total)).filter(
        Invoice.organization_id == org_id
    ).scalar() or Decimal("0.00")

    # 2. Monthly Expense Trend
    invoices = db.query(Invoice).filter(Invoice.organization_id == org_id).all()
    monthly_data: Dict[str, Dict[str, Any]] = {}
    
    # Pre-populate last 6 calendar months
    now = datetime.now(timezone.utc)
    for i in range(5, -1, -1):
        m_dt = (now.replace(day=1) - timedelta(days=i*28))
        key = m_dt.strftime("%b %Y")
        monthly_data[key] = {"month": key, "total": 0.0, "tax": 0.0, "count": 0}

    for inv in invoices:
        try:
            inv_dt = datetime.strptime(str(inv.invoice_date)[:10], "%Y-%m-%d")
            key = inv_dt.strftime("%b %Y")
            if key not in monthly_data:
                monthly_data[key] = {"month": key, "total": 0.0, "tax": 0.0, "count": 0}
            monthly_data[key]["total"] += float(inv.grand_total)
            monthly_data[key]["tax"] += float(inv.total_tax)
            monthly_data[key]["count"] += 1
        except Exception:
            pass

    trend_list = list(monthly_data.values())

    # 3. Status Distribution
    status_counts = db.query(
        Document.status, func.count(Document.id)
    ).filter(Document.organization_id == org_id).group_by(Document.status).all()

    status_dist = [{"name": s[0].replace("_", " ").title(), "value": s[1]} for s in status_counts]

    # 4. Document Type Distribution
    type_counts = db.query(
        Document.document_type, func.count(Document.id)
    ).filter(Document.organization_id == org_id).group_by(Document.document_type).all()

    type_dist = [{"name": t[0], "value": t[1]} for t in type_counts]

    # 5. Recent Activity
    logs = db.query(AuditLog).filter(
        AuditLog.organization_id == org_id
    ).order_by(desc(AuditLog.created_at)).limit(8).all()

    recent_acts = [
        {
            "id": l.id,
            "action": l.action.replace("_", " ").title(),
            "entity": l.entity_type,
            "timestamp": l.created_at.strftime("%Y-%m-%d %H:%M"),
            "details": l.details
        }
        for l in logs
    ]

    return DashboardMetricsOut(
        total_documents=total_docs,
        total_invoices=total_invoices,
        processed_documents=processed_docs,
        pending_approvals=pending_approvals,
        failed_documents=failed_docs,
        duplicate_warnings=duplicate_warnings,
        total_invoice_value=total_val,
        currency="INR",
        monthly_expense_trend=trend_list,
        processing_status_distribution=status_dist,
        document_type_distribution=type_dist,
        recent_activity=recent_acts
    )


@router.get("/expenses", response_model=List[ExpenseTrendItem])
def get_expense_report(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    invoices = db.query(Invoice).filter(Invoice.organization_id == auth_ctx.organization_id).all()
    grouped: Dict[str, Dict[str, Any]] = {}
    for inv in invoices:
        try:
            m = str(inv.invoice_date)[:7]  # YYYY-MM
            if m not in grouped:
                grouped[m] = {"month": m, "total_amount": Decimal("0.00"), "tax_amount": Decimal("0.00"), "count": 0}
            grouped[m]["total_amount"] += inv.grand_total
            grouped[m]["tax_amount"] += inv.total_tax
            grouped[m]["count"] += 1
        except Exception:
            pass

    return [
        ExpenseTrendItem(
            month=k,
            total_amount=v["total_amount"],
            tax_amount=v["tax_amount"],
            invoice_count=v["count"]
        )
        for k, v in sorted(grouped.items())
    ]


@router.get("/suppliers", response_model=List[SupplierSpendItem])
def get_supplier_spending(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    suppliers = db.query(Supplier).filter(Supplier.organization_id == auth_ctx.organization_id).all()
    total_spend_all = sum((s.total_spend for s in suppliers), Decimal("0.00"))

    result = []
    for s in sorted(suppliers, key=lambda x: x.total_spend, reverse=True):
        pct = (float(s.total_spend) / float(total_spend_all) * 100) if total_spend_all > 0 else 0.0
        result.append(SupplierSpendItem(
            supplier_id=s.id,
            supplier_name=s.name,
            total_spend=s.total_spend,
            invoice_count=s.invoice_count,
            percentage_of_total=round(pct, 2)
        ))
    return result


@router.post("/exports", response_model=ExportRecordOut)
def create_export(
    req: ExportRequest,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    org_id = auth_ctx.organization_id

    # Fetch data according to export_type
    records_to_export = []
    if req.export_type in ["INVOICES", "EXPENSES"]:
        invoices = db.query(Invoice).filter(Invoice.organization_id == org_id).all()
        for inv in invoices:
            records_to_export.append({
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date,
                "due_date": inv.due_date,
                "supplier_name": inv.supplier_name_raw,
                "supplier_gstin": inv.supplier_gstin_raw,
                "customer_name": inv.customer_name_raw,
                "currency": inv.currency,
                "taxable_amount": float(inv.taxable_amount),
                "cgst": float(inv.cgst),
                "sgst": float(inv.sgst),
                "igst": float(inv.igst),
                "total_tax": float(inv.total_tax),
                "grand_total": float(inv.grand_total),
                "status": inv.status
            })
    elif req.export_type == "SUPPLIERS":
        suppliers = db.query(Supplier).filter(Supplier.organization_id == org_id).all()
        for s in suppliers:
            records_to_export.append({
                "supplier_name": s.name,
                "gstin": s.gstin,
                "city": s.city,
                "state": s.state,
                "total_spend": float(s.total_spend),
                "invoice_count": s.invoice_count
            })

    # Generate File
    if req.format == "CSV":
        file_path, count = ExportEngine.generate_csv_report(records_to_export, req.export_type, org_id)
    else:
        file_path, count = ExportEngine.generate_excel_report(records_to_export, req.export_type, org_id)

    export_rec = ExportRecord(
        organization_id=org_id,
        user_id=auth_ctx.user.id,
        export_type=req.export_type,
        format=req.format,
        file_path=file_path,
        record_count=count,
        filters=req.filters or {}
    )
    db.add(export_rec)
    db.commit()
    db.refresh(export_rec)

    AuditService.log_event(
        db=db,
        organization_id=org_id,
        user_id=auth_ctx.user.id,
        action="EXPORT_GENERATED",
        entity_type="EXPORT",
        entity_id=export_rec.id,
        details={"type": req.export_type, "format": req.format, "record_count": count}
    )

    return export_rec


@router.get("/exports/{export_id}/download")
def download_export_file(
    export_id: str,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    rec = db.query(ExportRecord).filter(
        ExportRecord.id == export_id,
        ExportRecord.organization_id == auth_ctx.organization_id
    ).first()

    if not rec or not os.path.exists(rec.file_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    filename = os.path.basename(rec.file_path)
    media_type = "text/csv" if rec.format == "CSV" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(path=rec.file_path, filename=filename, media_type=media_type)
