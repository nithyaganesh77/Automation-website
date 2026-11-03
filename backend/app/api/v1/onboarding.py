import secrets
from typing import List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.all_models import (
    Organization, OrganizationSetting, OrganizationMember,
    OrganizationInvitation, Document, User
)
from app.schemas.onboarding import (
    OnboardingProfileRequest, InviteMemberRequest, InvitationOut,
    ConfigureAIRequest, OnboardingStatusOut
)
from app.api.deps import AuthenticatedContext, get_current_user_context, require_roles
from app.services.audit_service import AuditService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/onboarding", tags=["Customer Onboarding"])

VALID_ROLES = [
    "Super Admin",
    "Organization Owner",
    "Administrator",
    "Admin",
    "Accountant",
    "Reviewer",
    "Read-only User"
]


@router.get("/status", response_model=OnboardingStatusOut)
def get_onboarding_status(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """Returns the comprehensive customer onboarding status and progress checklist."""
    org = db.query(Organization).filter(Organization.id == auth_ctx.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    members_count = db.query(func.count(OrganizationMember.id)).filter(
        OrganizationMember.organization_id == org.id
    ).scalar() or 0

    invites_count = db.query(func.count(OrganizationInvitation.id)).filter(
        OrganizationInvitation.organization_id == org.id,
        OrganizationInvitation.status == "PENDING"
    ).scalar() or 0

    docs_count = db.query(func.count(Document.id)).filter(
        Document.organization_id == org.id
    ).scalar() or 0

    settings = db.query(OrganizationSetting).filter(
        OrganizationSetting.organization_id == org.id
    ).first()

    sub = SubscriptionService.get_or_create_subscription(db, org.id)

    profile_done = bool(org.legal_name or org.gstin or org.address)
    ai_configured = bool(settings and (settings.api_key_configured or settings.primary_provider))
    first_doc_done = docs_count > 0

    return OnboardingStatusOut(
        organization_id=org.id,
        organization_name=org.name,
        onboarding_completed=org.onboarding_completed,
        current_step=org.onboarding_step or "PROFILE",
        profile_completed=profile_done,
        team_members_count=members_count,
        pending_invites_count=invites_count,
        ai_configured=ai_configured,
        first_invoice_uploaded=first_doc_done,
        has_active_subscription=sub.status in ["TRIAL", "ACTIVE"]
    )


@router.post("/profile", response_model=OnboardingStatusOut)
def update_onboarding_profile(
    req: OnboardingProfileRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """Step 1: Updates organization business details, legal name, GSTIN, and location."""
    org = db.query(Organization).filter(Organization.id == auth_ctx.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if req.legal_name is not None:
        org.legal_name = req.legal_name
    if req.gstin is not None:
        org.gstin = req.gstin.strip().upper()
    if req.pan is not None:
        org.pan = req.pan.strip().upper()
    if req.address is not None:
        org.address = req.address
    if req.city is not None:
        org.city = req.city
    if req.state is not None:
        org.state = req.state
    if req.pincode is not None:
        org.pincode = req.pincode
    if req.phone is not None:
        org.phone = req.phone

    org.onboarding_step = "TEAM"
    db.commit()

    AuditService.log_event(
        db=db,
        organization_id=org.id,
        user_id=auth_ctx.user.id,
        action="ONBOARDING_PROFILE_UPDATED",
        entity_type="ORGANIZATION",
        entity_id=org.id,
        details={"legal_name": org.legal_name, "gstin": org.gstin}
    )

    return get_onboarding_status(auth_ctx=auth_ctx, db=db)


@router.post("/invite", response_model=InvitationOut)
def invite_employee(
    req: InviteMemberRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """Step 2: Invites an employee with a specific role."""
    if req.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{req.role}'. Must be one of: {', '.join(VALID_ROLES)}"
        )

    # Check for existing pending invite
    existing = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.organization_id == auth_ctx.organization_id,
        OrganizationInvitation.email == req.email.lower(),
        OrganizationInvitation.status == "PENDING"
    ).first()
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    invitation = OrganizationInvitation(
        organization_id=auth_ctx.organization_id,
        email=req.email.lower(),
        role=req.role,
        invited_by_user_id=auth_ctx.user.id,
        token=secrets.token_urlsafe(32),
        status="PENDING",
        expires_at=now + timedelta(days=7)
    )
    db.add(invitation)

    org = db.query(Organization).filter(Organization.id == auth_ctx.organization_id).first()
    if org and org.onboarding_step == "TEAM":
        org.onboarding_step = "AI_CONFIG"

    db.commit()
    db.refresh(invitation)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="EMPLOYEE_INVITED",
        entity_type="INVITATION",
        entity_id=invitation.id,
        details={"email": invitation.email, "role": invitation.role}
    )

    return invitation


@router.get("/invitations", response_model=List[InvitationOut])
def list_invitations(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """Lists all pending invitations for the current organization."""
    return db.query(OrganizationInvitation).filter(
        OrganizationInvitation.organization_id == auth_ctx.organization_id
    ).order_by(OrganizationInvitation.created_at.desc()).all()


@router.delete("/invitations/{invite_id}")
def revoke_invitation(
    invite_id: str,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """Revokes an outstanding invitation."""
    inv = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.id == invite_id,
        OrganizationInvitation.organization_id == auth_ctx.organization_id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")

    inv.status = "REVOKED"
    db.commit()
    return {"message": "Invitation revoked successfully."}


@router.post("/ai-config", response_model=OnboardingStatusOut)
def configure_organization_ai(
    req: ConfigureAIRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """Step 3: Configures organization-level AI provider preferences."""
    settings = db.query(OrganizationSetting).filter(
        OrganizationSetting.organization_id == auth_ctx.organization_id
    ).first()

    if not settings:
        settings = OrganizationSetting(organization_id=auth_ctx.organization_id)
        db.add(settings)

    settings.primary_provider = req.primary_provider
    settings.fallback_provider = req.fallback_provider
    if req.confidence_threshold:
        settings.confidence_threshold = req.confidence_threshold
    if req.monthly_budget_usd:
        settings.monthly_budget_usd = req.monthly_budget_usd

    if req.gemini_api_key:
        settings.gemini_api_key_masked = f"{req.gemini_api_key[:4]}...{req.gemini_api_key[-4:]}"
        settings.api_key_configured = True
    if req.groq_api_key:
        settings.groq_api_key_masked = f"{req.groq_api_key[:4]}...{req.groq_api_key[-4:]}"
        settings.api_key_configured = True

    org = db.query(Organization).filter(Organization.id == auth_ctx.organization_id).first()
    if org and org.onboarding_step in ["TEAM", "AI_CONFIG"]:
        org.onboarding_step = "FIRST_INVOICE"

    db.commit()

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="AI_SETTINGS_CONFIGURED",
        entity_type="ORGANIZATION_SETTING",
        entity_id=settings.id,
        details={"primary": req.primary_provider, "fallback": req.fallback_provider}
    )

    return get_onboarding_status(auth_ctx=auth_ctx, db=db)


@router.post("/complete", response_model=OnboardingStatusOut)
def complete_onboarding(
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """Step 4: Finalizes customer onboarding and activates full platform access."""
    org = db.query(Organization).filter(Organization.id == auth_ctx.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.onboarding_completed = True
    org.onboarding_step = "COMPLETED"
    db.commit()

    AuditService.log_event(
        db=db,
        organization_id=org.id,
        user_id=auth_ctx.user.id,
        action="ONBOARDING_COMPLETED",
        entity_type="ORGANIZATION",
        entity_id=org.id,
        details={"completed_at": datetime.now(timezone.utc).isoformat()}
    )

    return get_onboarding_status(auth_ctx=auth_ctx, db=db)

