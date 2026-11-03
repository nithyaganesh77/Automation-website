import os
from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.session import get_db, check_db_health
from app.models.all_models import (
    Organization, User, Document, Invoice, OrganizationMember,
    Subscription, AgentExecution, AuditLog
)
from app.schemas.super_admin import (
    SuperAdminMetricsOut, OrganizationOverviewOut, SystemHealthOut
)
from app.api.deps import AuthenticatedContext, get_current_user_context
from app.services.llm import LLMService
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Super Admin"])


def require_super_admin(auth_ctx: AuthenticatedContext = Depends(get_current_user_context)) -> AuthenticatedContext:
    """Restricts access exclusively to global Super Administrators."""
    if not auth_ctx.user.is_superuser and auth_ctx.role != "Super Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Global platform administrator privileges required."
        )
    return auth_ctx


@router.get("/metrics", response_model=SuperAdminMetricsOut)
def get_super_admin_metrics(
    auth_ctx: AuthenticatedContext = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """
    Computes cross-tenant global analytics for platform operators:
    - Total orgs, users, documents
    - Storage volume
    - AI provider telemetry & cost
    - Subscription statuses
    - Live health checks
    """
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_docs = db.query(func.count(Document.id)).scalar() or 0
    
    total_spend = db.query(func.sum(Invoice.grand_total)).scalar() or 0.0
    failed_docs = db.query(func.count(Document.id)).filter(Document.status == "FAILED").scalar() or 0
    total_bytes = db.query(func.sum(Document.file_size)).scalar() or 0

    # Subscriptions breakdown
    subs = db.query(Subscription.plan_tier, func.count(Subscription.id)).group_by(Subscription.plan_tier).all()
    sub_map = {tier: count for tier, count in subs}

    # Storage consumption check
    upload_path = Path(settings.UPLOAD_DIR)
    disk_used_bytes = 0
    if upload_path.exists():
        disk_used_bytes = sum(f.stat().st_size for f in upload_path.rglob('*') if f.is_file())

    # Organizations summary
    orgs = db.query(Organization).order_by(desc(Organization.created_at)).limit(20).all()
    recent_orgs = []
    for o in orgs:
        m_count = db.query(func.count(OrganizationMember.id)).filter(OrganizationMember.organization_id == o.id).scalar() or 0
        d_count = db.query(func.count(Document.id)).filter(Document.organization_id == o.id).scalar() or 0
        i_sum = db.query(func.sum(Invoice.grand_total)).filter(Invoice.organization_id == o.id).scalar() or 0.0
        s = db.query(Subscription).filter(Subscription.organization_id == o.id).first()

        recent_orgs.append(OrganizationOverviewOut(
            id=o.id,
            name=o.name,
            slug=o.slug,
            legal_name=o.legal_name,
            gstin=o.gstin,
            created_at=o.created_at,
            members_count=m_count,
            documents_count=d_count,
            invoices_total_amount=float(i_sum),
            subscription_plan=s.plan_tier if s else "STARTER",
            subscription_status=s.status if s else "TRIAL",
            onboarding_completed=o.onboarding_completed
        ))

    # AI usage telemetry
    ai_telemetry = LLMService.get_telemetry()
    db_health = check_db_health()

    system_health = SystemHealthOut(
        status="healthy" if db_health.get("status") == "healthy" else "degraded",
        database=db_health,
        ai_engine={
            "primary": settings.AI_PRIMARY_PROVIDER,
            "fallback": settings.AI_FALLBACK_PROVIDER,
            "gemini_status": ai_telemetry.get("gemini_status"),
            "groq_status": ai_telemetry.get("groq_status")
        },
        storage={
            "storage_type": settings.STORAGE_TYPE,
            "disk_used_bytes": disk_used_bytes,
            "disk_used_mb": round(disk_used_bytes / (1024 * 1024), 2)
        },
        active_daemons={
            "fastapi": "running",
            "celery": "fallback_async" if not settings.CELERY_BROKER_URL else "connected"
        }
    )

    return SuperAdminMetricsOut(
        total_organizations=total_orgs,
        total_users=total_users,
        total_documents=total_docs,
        total_invoices_value_inr=float(total_spend),
        total_processed_volume_bytes=total_bytes,
        failed_processing_jobs_count=failed_docs,
        ai_metrics=ai_telemetry,
        storage_consumption={
            "disk_bytes": disk_used_bytes,
            "disk_formatted": f"{disk_used_bytes / (1024 * 1024):.2f} MB"
        },
        subscriptions_breakdown=sub_map,
        system_health=system_health,
        recent_organizations=recent_orgs
    )


@router.get("/organizations", response_model=List[OrganizationOverviewOut])
def list_all_organizations(
    auth_ctx: AuthenticatedContext = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Lists all registered organizations across the platform."""
    orgs = db.query(Organization).order_by(desc(Organization.created_at)).all()
    result = []
    for o in orgs:
        m_count = db.query(func.count(OrganizationMember.id)).filter(OrganizationMember.organization_id == o.id).scalar() or 0
        d_count = db.query(func.count(Document.id)).filter(Document.organization_id == o.id).scalar() or 0
        i_sum = db.query(func.sum(Invoice.grand_total)).filter(Invoice.organization_id == o.id).scalar() or 0.0
        s = db.query(Subscription).filter(Subscription.organization_id == o.id).first()

        result.append(OrganizationOverviewOut(
            id=o.id,
            name=o.name,
            slug=o.slug,
            legal_name=o.legal_name,
            gstin=o.gstin,
            created_at=o.created_at,
            members_count=m_count,
            documents_count=d_count,
            invoices_total_amount=float(i_sum),
            subscription_plan=s.plan_tier if s else "STARTER",
            subscription_status=s.status if s else "TRIAL",
            onboarding_completed=o.onboarding_completed
        ))
    return result

