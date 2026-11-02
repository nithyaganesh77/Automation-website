from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AgentStatusSummary(BaseModel):
    agent_id: str
    name: str
    purpose: str
    status: str  # ACTIVE, IDLE, ERROR
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_latency_ms: float
    last_execution_at: Optional[datetime] = None
    last_error: Optional[str] = None


class AgentTraceOut(BaseModel):
    id: str
    document_id: str
    agent_name: str
    status: str
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    latency_ms: int
    tokens_used: int
    cost_usd: float
    created_at: datetime

    class Config:
        from_attributes = True
