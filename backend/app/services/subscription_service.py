import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Tuple, List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.all_models import (
    Subscription, Organization, OrganizationMember, Document
)
from app.core.config import settings

COMMERCIAL_PLANS = {
    "STARTER": {
        "name": "Starter Plan",
        "description": "Essential automated invoice extraction and audit for small businesses.",
        "monthly_price_inr": 2499.00,
        "annual_price_inr": 24990.00,  # 2 months free
        "monthly_document_limit": 50,
        "max_users_limit": 3,
        "features": [
            "Up to 50 invoices & bills per month",
            "Up to 3 team members",
            "Deterministic Indian GST validation",
            "Duplicate invoice detection",
            "Standard Excel ledger exports",
            "Dual AI provider failover (Gemini + Groq)"
        ],
        "highlighted": False
    },
    "PROFESSIONAL": {
        "name": "Professional Plan",
        "description": "Comprehensive document intelligence and vendor risk automation for growing businesses.",
        "monthly_price_inr": 9999.00,
        "annual_price_inr": 99990.00,
        "monthly_document_limit": 500,
        "max_users_limit": 15,
        "features": [
            "Up to 500 documents per month",
            "Up to 15 team members with role-based access",
            "Advanced multi-agent spend anomaly detection",
            "Vendor median spend baseline analytics",
            "Custom approval routing rules & thresholds",
            "Priority LLM inference queue",
            "Audit log export & compliance history"
        ],
        "highlighted": True
    },
    "ENTERPRISE": {
        "name": "Enterprise Plan",
        "description": "High-throughput autonomous processing, multi-department segregation and custom SLA.",
        "monthly_price_inr": 29999.00,
        "annual_price_inr": 299990.00,
        "monthly_document_limit": 5000,
        "max_users_limit": 100,
        "features": [
            "5,000+ monthly documents (custom scaling)",
            "Unlimited departments & up to 100 users",
            "Complete multi-tenant data segregation",
            "Dedicated customer-hosted or on-premise installation option",
            "Custom ERP and accounting API integrations",
            "Bring-your-own Gemini / Groq API keys",
            "Dedicated Enterprise SLA & 24/7 priority support"
        ],
        "highlighted": False
    }
}


class SubscriptionService:
    @classmethod
    def get_or_create_subscription(cls, db: Session, organization_id: str) -> Subscription:
        """
        Retrieves existing organization subscription or provisions a 14-day free TRIAL.
        """
        sub = db.query(Subscription).filter(Subscription.organization_id == organization_id).first()
        if not sub:
            now = datetime.now(timezone.utc)
            trial_end = now + timedelta(days=14)
            period_end = now + timedelta(days=30)
            starter = COMMERCIAL_PLANS["STARTER"]

            sub = Subscription(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                plan_tier="STARTER",
                status="TRIAL",
                monthly_document_limit=starter["monthly_document_limit"],
                max_users_limit=starter["max_users_limit"],
                current_period_documents_used=0,
                current_period_start=now,
                current_period_end=period_end,
                trial_ends_at=trial_end,
                billing_cycle="MONTHLY",
                price_amount=Decimal(str(starter["monthly_price_inr"])),
                currency="INR"
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)
        return sub

    @classmethod
    def check_upload_quota(cls, db: Session, organization_id: str) -> Tuple[bool, str]:
        """
        Enforces commercial usage constraints:
        - Checks subscription expiration or past-due status.
        - Checks whether monthly document upload limits have been reached.
        Returns: (can_upload: bool, reason: str)
        """
        sub = cls.get_or_create_subscription(db, organization_id)
        now = datetime.now(timezone.utc)

        # 1. Check expiration for TRIAL
        if sub.status == "TRIAL" and sub.trial_ends_at:
            # Handle tz-naive vs tz-aware
            trial_end = sub.trial_ends_at if sub.trial_ends_at.tzinfo else sub.trial_ends_at.replace(tzinfo=timezone.utc)
            if now > trial_end:
                sub.status = "EXPIRED"
                db.commit()
                return False, f"Your 14-day free trial expired on {trial_end.strftime('%Y-%m-%d')}. Please upgrade your plan to continue processing documents."

        if sub.status in ["EXPIRED", "CANCELLED", "PAST_DUE"]:
            return False, f"Subscription is currently {sub.status}. Please update your commercial plan to resume document automation."

        # 2. Check monthly usage counter against plan limit
        # Auto-reset if new monthly billing period has started
        if sub.current_period_end:
            p_end = sub.current_period_end if sub.current_period_end.tzinfo else sub.current_period_end.replace(tzinfo=timezone.utc)
            if now > p_end:
                sub.current_period_start = now
                sub.current_period_end = now + timedelta(days=30)
                sub.current_period_documents_used = 0
                db.commit()

        if sub.current_period_documents_used >= sub.monthly_document_limit:
            return False, (
                f"Monthly document limit reached ({sub.current_period_documents_used}/{sub.monthly_document_limit} documents on {sub.plan_tier} plan). "
                "Please upgrade your subscription tier to process additional documents."
            )

        return True, "Quota verified."

    @classmethod
    def increment_document_count(cls, db: Session, organization_id: str):
        """Increments the monthly document consumption counter."""
        sub = cls.get_or_create_subscription(db, organization_id)
        sub.current_period_documents_used += 1
        db.commit()
        db.refresh(sub)

    @classmethod
    def change_plan(
        cls, 
        db: Session, 
        organization_id: str, 
        target_plan: str, 
        billing_cycle: str = "MONTHLY"
    ) -> Subscription:
        """
        Updates organization subscription plan and limits.
        Architecture ready for future Razorpay webhooks.
        """
        if target_plan not in COMMERCIAL_PLANS:
            raise ValueError(f"Invalid plan tier: {target_plan}")

        plan_info = COMMERCIAL_PLANS[target_plan]
        sub = cls.get_or_create_subscription(db, organization_id)
        now = datetime.now(timezone.utc)

        sub.plan_tier = target_plan
        sub.status = "ACTIVE"
        sub.billing_cycle = billing_cycle
        sub.monthly_document_limit = plan_info["monthly_document_limit"]
        sub.max_users_limit = plan_info["max_users_limit"]
        
        price = plan_info["annual_price_inr"] if billing_cycle == "ANNUAL" else plan_info["monthly_price_inr"]
        sub.price_amount = Decimal(str(price))
        sub.current_period_start = now
        sub.current_period_end = now + (timedelta(days=365) if billing_cycle == "ANNUAL" else timedelta(days=30))
        
        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def verify_webhook_signature(cls, raw_body: bytes, signature: Optional[str]) -> bool:
        """Cryptographically verifies Razorpay webhook HMAC SHA256 signature."""
        if not signature:
            return False
        import hmac
        import hashlib
        secret = settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8")
        expected = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    @classmethod
    def handle_webhook_event(cls, db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes commercial payment gateway events (Razorpay compatible):
        - subscription.activated
        - subscription.charged / invoice.paid
        - payment.failed
        - subscription.cancelled / subscription.completed
        """
        event = payload.get("event", "")
        entity = (
            payload.get("payload", {}).get("subscription", {}).get("entity", {})
            or payload.get("payload", {}).get("payment", {}).get("entity", {})
        )

        sub_id = entity.get("id") or entity.get("subscription_id")
        notes = entity.get("notes", {})
        org_id = notes.get("organization_id")

        sub = None
        if org_id:
            sub = db.query(Subscription).filter(Subscription.organization_id == org_id).first()
        elif sub_id:
            sub = db.query(Subscription).filter(Subscription.razorpay_subscription_id == sub_id).first()

        if not sub:
            return {"status": "ignored", "reason": "No matching organization subscription found", "event": event}

        now = datetime.now(timezone.utc)
        if event in ["subscription.activated", "subscription.authenticated"]:
            sub.status = "ACTIVE"
            sub.razorpay_subscription_id = sub_id
        elif event in ["subscription.charged", "invoice.paid"]:
            sub.status = "ACTIVE"
            sub.current_period_documents_used = 0  # reset monthly quota on successful payment
            sub.current_period_start = now
            sub.current_period_end = now + timedelta(days=30)
        elif event in ["payment.failed", "subscription.pending"]:
            sub.status = "PAST_DUE"
        elif event in ["subscription.cancelled", "subscription.completed"]:
            sub.status = "CANCELLED"

        db.commit()
        db.refresh(sub)
        return {
            "status": "processed",
            "event": event,
            "organization_id": sub.organization_id,
            "subscription_status": sub.status,
            "plan_tier": sub.plan_tier
        }

