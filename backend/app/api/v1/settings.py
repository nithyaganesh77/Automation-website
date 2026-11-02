from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.session import get_db
from app.models.all_models import OrganizationSetting, AuditLog
from app.schemas.report import (
    SettingsOut, SettingsUpdateRequest, TestConnectionRequest,
    TestConnectionResponse, AIUsageTelemetryOut
)
from app.api.deps import AuthenticatedContext, get_current_user_context, require_roles
from app.core.config import settings as app_settings
from app.services.llm import LLMService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/settings", tags=["Settings & AI Telemetry"])


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
            api_key_configured=bool(app_settings.GEMINI_API_KEY or app_settings.GROQ_API_KEY),
            confidence_threshold=0.85,
            tax_tolerance=2.00,
            auto_approve_threshold=0.98,
            currency="INR"
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

    telemetry = LLMService.get_telemetry()

    return SettingsOut(
        primary_provider=app_settings.AI_PRIMARY_PROVIDER,
        fallback_provider=app_settings.AI_FALLBACK_PROVIDER,
        gemini_model=app_settings.GEMINI_MODEL,
        groq_model=app_settings.GROQ_MODEL,
        gemini_configured=bool(app_settings.GEMINI_API_KEY),
        groq_configured=bool(app_settings.GROQ_API_KEY),
        gemini_status=telemetry["gemini_status"],
        groq_status=telemetry["groq_status"],
        disable_external_ai=app_settings.DISABLE_EXTERNAL_AI,
        daily_request_limit=app_settings.DAILY_REQUEST_LIMIT,
        monthly_token_budget=app_settings.MONTHLY_TOKEN_BUDGET,
        safe_quota_mode=app_settings.SAFE_QUOTA_MODE,
        confidence_threshold=setting.confidence_threshold,
        tax_tolerance=setting.tax_tolerance,
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

    if req.primary_provider is not None:
        app_settings.AI_PRIMARY_PROVIDER = req.primary_provider
        setting.ai_provider = req.primary_provider
    if req.fallback_provider is not None:
        app_settings.AI_FALLBACK_PROVIDER = req.fallback_provider
    if req.gemini_model is not None:
        app_settings.GEMINI_MODEL = req.gemini_model
    if req.groq_model is not None:
        app_settings.GROQ_MODEL = req.groq_model

    if req.gemini_api_key is not None and req.gemini_api_key.strip():
        app_settings.GEMINI_API_KEY = req.gemini_api_key.strip()
    if req.groq_api_key is not None and req.groq_api_key.strip():
        app_settings.GROQ_API_KEY = req.groq_api_key.strip()

    if req.disable_external_ai is not None:
        app_settings.DISABLE_EXTERNAL_AI = req.disable_external_ai
    if req.daily_request_limit is not None:
        app_settings.DAILY_REQUEST_LIMIT = req.daily_request_limit
    if req.monthly_token_budget is not None:
        app_settings.MONTHLY_TOKEN_BUDGET = req.monthly_token_budget
    if req.safe_quota_mode is not None:
        app_settings.SAFE_QUOTA_MODE = req.safe_quota_mode

    if req.confidence_threshold is not None:
        setting.confidence_threshold = req.confidence_threshold
    if req.tax_tolerance is not None:
        setting.tax_tolerance = req.tax_tolerance
    if req.currency is not None:
        setting.currency = req.currency

    setting.api_key_configured = bool(app_settings.GEMINI_API_KEY or app_settings.GROQ_API_KEY)
    db.commit()
    db.refresh(setting)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="SETTINGS_AND_AI_PROVIDERS_UPDATED",
        entity_type="ORGANIZATION_SETTING",
        entity_id=setting.id,
        details={
            "primary": app_settings.AI_PRIMARY_PROVIDER,
            "fallback": app_settings.AI_FALLBACK_PROVIDER,
            "privacy_mode": app_settings.DISABLE_EXTERNAL_AI
        }
    )

    telemetry = LLMService.get_telemetry()
    return SettingsOut(
        primary_provider=app_settings.AI_PRIMARY_PROVIDER,
        fallback_provider=app_settings.AI_FALLBACK_PROVIDER,
        gemini_model=app_settings.GEMINI_MODEL,
        groq_model=app_settings.GROQ_MODEL,
        gemini_configured=bool(app_settings.GEMINI_API_KEY),
        groq_configured=bool(app_settings.GROQ_API_KEY),
        gemini_status=telemetry["gemini_status"],
        groq_status=telemetry["groq_status"],
        disable_external_ai=app_settings.DISABLE_EXTERNAL_AI,
        daily_request_limit=app_settings.DAILY_REQUEST_LIMIT,
        monthly_token_budget=app_settings.MONTHLY_TOKEN_BUDGET,
        safe_quota_mode=app_settings.SAFE_QUOTA_MODE,
        confidence_threshold=setting.confidence_threshold,
        tax_tolerance=setting.tax_tolerance,
        currency=setting.currency
    )


@router.post("/test-connection", response_model=TestConnectionResponse)
def test_provider_connection(
    req: TestConnectionRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin"]))
):
    key = req.api_key
    if not key:
        if req.provider == "gemini":
            key = app_settings.GEMINI_API_KEY
        elif req.provider == "groq":
            key = app_settings.GROQ_API_KEY

    if not key:
        return TestConnectionResponse(
            success=False,
            message=f"No API key configured for {req.provider}. Please supply a key to test."
        )

    success, msg = LLMService.test_provider_connection(req.provider, key)
    return TestConnectionResponse(success=success, message=msg)


@router.get("/telemetry", response_model=AIUsageTelemetryOut)
def get_ai_usage_telemetry(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context)
):
    telemetry = LLMService.get_telemetry()
    return AIUsageTelemetryOut(**telemetry)


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
