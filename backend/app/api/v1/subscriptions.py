from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.all_models import Subscription, Organization, OrganizationMember, Document
from app.schemas.subscription import (
    PlanDetailsOut, SubscriptionStatusOut, UpgradePlanRequest
)
from app.api.deps import AuthenticatedContext, get_current_user_context, require_roles
from app.services.subscription_service import SubscriptionService, COMMERCIAL_PLANS
from app.services.audit_service import AuditService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions & Billing"])


@router.get("/plans", response_model=List[PlanDetailsOut])
def get_commercial_plans():
    """Lists all available commercial subscription tiers and included features."""
    plans = []
    for tier, p in COMMERCIAL_PLANS.items():
        plans.append(PlanDetailsOut(
            tier=tier,
            name=p["name"],
            description=p["description"],
            monthly_price_inr=p["monthly_price_inr"],
            annual_price_inr=p["annual_price_inr"],
            monthly_document_limit=p["monthly_document_limit"],
            max_users_limit=p["max_users_limit"],
            features=p["features"],
            highlighted=p["highlighted"]
        ))
    return plans


@router.get("/current", response_model=SubscriptionStatusOut)
def get_current_subscription(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    """Retrieves current subscription status, live usage counter, and limits."""
    sub = SubscriptionService.get_or_create_subscription(db, auth_ctx.organization_id)
    
    users_count = db.query(func.count(OrganizationMember.id)).filter(
        OrganizationMember.organization_id == auth_ctx.organization_id
    ).scalar() or 0

    can_upload, _ = SubscriptionService.check_upload_quota(db, auth_ctx.organization_id)

    # Calculate trial days remaining
    trial_days = None
    is_trial = sub.status == "TRIAL"
    if is_trial and sub.trial_ends_at:
        now = datetime.now(timezone.utc)
        t_end = sub.trial_ends_at if sub.trial_ends_at.tzinfo else sub.trial_ends_at.replace(tzinfo=timezone.utc)
        diff = (t_end - now).days
        trial_days = max(diff, 0)

    usage_pct = 0.0
    if sub.monthly_document_limit > 0:
        usage_pct = round((sub.current_period_documents_used / sub.monthly_document_limit) * 100, 1)

    return SubscriptionStatusOut(
        plan_tier=sub.plan_tier,
        status=sub.status,
        is_trial=is_trial,
        trial_days_remaining=trial_days,
        documents_used=sub.current_period_documents_used,
        monthly_document_limit=sub.monthly_document_limit,
        users_count=users_count,
        max_users_limit=sub.max_users_limit,
        can_upload=can_upload,
        usage_percentage=min(usage_pct, 100.0),
        billing_cycle=sub.billing_cycle,
        price_amount=float(sub.price_amount or 0.0),
        currency=sub.currency,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end
    )


@router.post("/upgrade", response_model=SubscriptionStatusOut)
def upgrade_subscription(
    req: UpgradePlanRequest,
    auth_ctx: AuthenticatedContext = Depends(require_roles(["Admin", "Organization Owner"])),
    db: Session = Depends(get_db)
):
    """
    Upgrades or downgrades organization plan.
    Prepared for future Razorpay payment integration without making external paid API calls.
    """
    try:
        sub = SubscriptionService.change_plan(
            db=db,
            organization_id=auth_ctx.organization_id,
            target_plan=req.target_plan.upper(),
            billing_cycle=req.billing_cycle.upper()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="SUBSCRIPTION_PLAN_CHANGED",
        entity_type="SUBSCRIPTION",
        entity_id=sub.id,
        details={"plan": sub.plan_tier, "cycle": sub.billing_cycle, "status": sub.status}
    )

    return get_current_subscription(auth_ctx=auth_ctx, db=db)

