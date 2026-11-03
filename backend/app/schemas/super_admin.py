from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class SystemHealthOut(BaseModel):
    status: str
    database: Dict[str, Any]
    ai_engine: Dict[str, Any]
    storage: Dict[str, Any]
    active_daemons: Dict[str, Any]


class OrganizationOverviewOut(BaseModel):
    id: str
    name: str
    slug: str
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    created_at: datetime
    members_count: int
    documents_count: int
    invoices_total_amount: float
    subscription_plan: str
    subscription_status: str
    onboarding_completed: bool


class SuperAdminMetricsOut(BaseModel):
    total_organizations: int
    total_users: int
    total_documents: int
    total_invoices_value_inr: float
    total_processed_volume_bytes: int
    failed_processing_jobs_count: int
    ai_metrics: Dict[str, Any]
    storage_consumption: Dict[str, Any]
    subscriptions_breakdown: Dict[str, int]
    system_health: SystemHealthOut
    recent_organizations: List[OrganizationOverviewOut]

