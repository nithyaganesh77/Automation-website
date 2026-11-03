from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class OnboardingProfileRequest(BaseModel):
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    currency: Optional[str] = "INR"


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field(
        default="Reviewer",
        description="Role: Super Admin, Organization Owner, Administrator, Accountant, Reviewer, Read-only User"
    )


class InvitationOut(BaseModel):
    id: str
    organization_id: str
    email: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ConfigureAIRequest(BaseModel):
    primary_provider: str = Field(default="gemini", description="gemini or groq")
    fallback_provider: str = Field(default="groq", description="groq or gemini")
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    confidence_threshold: Optional[float] = 0.85
    monthly_budget_usd: Optional[float] = 100.0


class OnboardingStatusOut(BaseModel):
    organization_id: str
    organization_name: str
    onboarding_completed: bool
    current_step: str  # PROFILE, TEAM, AI_CONFIG, FIRST_INVOICE, COMPLETED
    profile_completed: bool
    team_members_count: int
    pending_invites_count: int
    ai_configured: bool
    first_invoice_uploaded: bool
    has_active_subscription: bool

