from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.session import get_db
from app.models.all_models import OrganizationSetting, AuditLog
from app.schemas.report import SettingsOut, SettingsUpdateRequest
from app.api.deps import AuthenticatedContext, get_current_user_context, require_roles
from app.core.config import settings as app_settings
from app.services.audit_service import AuditService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsOut)
def get_settings(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    setting = db.query(OrganizationSetting).filter(
        OrganizationSetting.organization_id == auth_ctx.organization_id
    ).first()

    if not setting:
        setting = OrganizationSetting(
            organization_id=auth_ctx.organization_id,
            ai_provider="gemini",
            api_key_configured=bool(app_settings.GEMINI_API_KEY),
            confidence_threshold=0.85,
            tax_tolerance=2.00,
            auto_approve_threshold=0.98,
            currency="INR"
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return SettingsOut(
        ai_provider=setting.ai_provider,
        api_key_configured=setting.api_key_configured or bool(app_settings.GEMINI_API_KEY or app_settings.OPENAI_API_KEY),
        confidence_threshold=setting.confidence_threshold,
        tax_tolerance=setting.tax_tolerance,
        auto_approve_threshold=setting.auto_approve_threshold,
        currency=setting.currency
    )


@router.patch("", response_model=SettingsOut)
def update_settings(
    req: SettingsUpdateRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin"])),
    db: Session = Depends(get_db)
):
    setting = db.query(OrganizationSetting).filter(
        OrganizationSetting.organization_id == auth_ctx.organization_id
    ).first()

    if not setting:
        setting = OrganizationSetting(organization_id=auth_ctx.organization_id)
        db.add(setting)

    if req.ai_provider is not None:
        setting.ai_provider = req.ai_provider
    if req.confidence_threshold is not None:
        setting.confidence_threshold = req.confidence_threshold
    if req.tax_tolerance is not None:
        setting.tax_tolerance = req.tax_tolerance
    if req.auto_approve_threshold is not None:
        setting.auto_approve_threshold = req.auto_approve_threshold
    if req.currency is not None:
        setting.currency = req.currency

    if req.gemini_api_key:
        app_settings.GEMINI_API_KEY = req.gemini_api_key
        setting.api_key_configured = True
    if req.openai_api_key:
        app_settings.OPENAI_API_KEY = req.openai_api_key
        setting.api_key_configured = True

    db.commit()
    db.refresh(setting)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="SETTINGS_UPDATED",
        entity_type="ORGANIZATION_SETTING",
        entity_id=setting.id
    )

    return SettingsOut(
        ai_provider=setting.ai_provider,
        api_key_configured=setting.api_key_configured,
        confidence_threshold=setting.confidence_threshold,
        tax_tolerance=setting.tax_tolerance,
        auto_approve_threshold=setting.auto_approve_threshold,
        currency=setting.currency
    )


@router.get("/audit-logs")
def get_audit_logs(
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin"])),
    db: Session = Depends(get_db),
    limit: int = 50
):
    logs = db.query(AuditLog).filter(
        AuditLog.organization_id == auth_ctx.organization_id
    ).order_by(desc(AuditLog.created_at)).limit(limit).all()

    return [
        {
            "id": l.id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "timestamp": l.created_at,
            "details": l.details
        }
        for l in logs
    ]
