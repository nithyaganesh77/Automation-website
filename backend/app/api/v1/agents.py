from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.session import get_db
from app.models.all_models import AgentExecution, Document
from app.schemas.agent import AgentStatusSummary, AgentTraceOut
from app.api.deps import AuthenticatedContext, get_current_user_context

router = APIRouter(prefix="/agents", tags=["Agents"])

STANDARD_AGENTS = [
    {"name": "Document Intake Agent", "purpose": "Document reception, MIME validation, SHA-256 generation, and duplicate checks."},
    {"name": "OCR Agent", "purpose": "Multi-page text extraction, PDF native parsing, scanned layout extraction."},
    {"name": "Classification Agent", "purpose": "Intelligent categorization into invoices, POs, receipts, bills, and contracts."},
    {"name": "Extraction Agent", "purpose": "Structured JSON schema field and line item extraction with evidence tracking."},
    {"name": "Validation Agent", "purpose": "Deterministic financial math reconciliation, GSTIN checksums, and date logic."},
    {"name": "Duplicate Detection Agent", "purpose": "Cryptographic file hash matching, vendor invoice deduplication, and fuzzy search."},
    {"name": "Anomaly Detection Agent", "purpose": "Statistical vendor spend variance, tax rate anomalies, and pattern deviations."},
    {"name": "Decision Agent", "purpose": "Confidence threshold evaluation and human approval routing orchestration."},
    {"name": "Reporting and Finalization Agent", "purpose": "PostgreSQL data persistence and accounting export readiness."}
]


@router.get("", response_model=List[AgentStatusSummary])
def get_agents_status(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    summaries = []
    
    # Query metrics scoped to organization documents
    for idx, agent_def in enumerate(STANDARD_AGENTS):
        agent_name = agent_def["name"]
        
        stats = db.query(
            func.count(AgentExecution.id).label("total"),
            func.avg(AgentExecution.latency_ms).label("avg_latency")
        ).join(Document).filter(
            Document.organization_id == auth_ctx.organization_id,
            AgentExecution.agent_name == agent_name
        ).first()

        success_count = db.query(func.count(AgentExecution.id)).join(Document).filter(
            Document.organization_id == auth_ctx.organization_id,
            AgentExecution.agent_name == agent_name,
            AgentExecution.status == "COMPLETED"
        ).scalar() or 0

        failed_count = db.query(func.count(AgentExecution.id)).join(Document).filter(
            Document.organization_id == auth_ctx.organization_id,
            AgentExecution.agent_name == agent_name,
            AgentExecution.status == "FAILED"
        ).scalar() or 0

        last_exec = db.query(AgentExecution).join(Document).filter(
            Document.organization_id == auth_ctx.organization_id,
            AgentExecution.agent_name == agent_name
        ).order_by(desc(AgentExecution.created_at)).first()

        summaries.append(AgentStatusSummary(
            agent_id=f"agent-{idx + 1}",
            name=agent_name,
            purpose=agent_def["purpose"],
            status="ERROR" if failed_count > 0 and (failed_count / max(stats.total or 1, 1)) > 0.5 else ("ACTIVE" if stats.total else "IDLE"),
            total_executions=stats.total or 0,
            successful_executions=success_count,
            failed_executions=failed_count,
            avg_latency_ms=round(float(stats.avg_latency or 0), 1),
            last_execution_at=last_exec.created_at if last_exec else None,
            last_error=last_exec.error_message if last_exec and last_exec.error_message else None
        ))

    return summaries


@router.get("/executions", response_model=List[AgentTraceOut])
def get_agent_executions(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db),
    agent_name: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    query = db.query(AgentExecution).join(Document).filter(
        Document.organization_id == auth_ctx.organization_id
    )

    if agent_name:
        query = query.filter(AgentExecution.agent_name == agent_name)
    if document_id:
        query = query.filter(AgentExecution.document_id == document_id)

    return query.order_by(desc(AgentExecution.created_at)).limit(limit).all()


@router.get("/executions/{execution_id}", response_model=AgentTraceOut)
def get_agent_execution_detail(
    execution_id: str,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    record = db.query(AgentExecution).join(Document).filter(
        AgentExecution.id == execution_id,
        Document.organization_id == auth_ctx.organization_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Execution trace not found")

    return record
