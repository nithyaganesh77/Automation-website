from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class PlanFeature(BaseModel):
    name: str
    included: bool


class PlanDetailsOut(BaseModel):
    tier: str
    name: str
    description: str
    monthly_price_inr: float
    annual_price_inr: float
    monthly_document_limit: int
    max_users_limit: int
    features: List[str]
    highlighted: bool = False


class SubscriptionStatusOut(BaseModel):
    plan_tier: str
    status: str  # TRIAL, ACTIVE, PAST_DUE, CANCELLED, EXPIRED
    is_trial: bool
    trial_days_remaining: Optional[int] = None
    documents_used: int
    monthly_document_limit: int
    users_count: int
    max_users_limit: int
    can_upload: bool
    usage_percentage: float
    billing_cycle: str
    price_amount: float
    currency: str
    current_period_start: datetime
    current_period_end: Optional[datetime] = None


class UpgradePlanRequest(BaseModel):
    target_plan: str = Field(description="STARTER, PROFESSIONAL, ENTERPRISE")
    billing_cycle: str = Field(default="MONTHLY", description="MONTHLY or ANNUAL")

