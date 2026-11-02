from typing import TypedDict, List, Dict, Any, Optional
from decimal import Decimal


class DocuMindState(TypedDict, total=False):
    # Document Identity
    document_id: str
    organization_id: str
    user_id: Optional[str]
    file_path: str
    file_name: str
    file_hash: str
    mime_type: str
    file_size: int

    # Agent 2: OCR Output
    pages: List[Dict[str, Any]]
    full_text: str

    # Agent 3: Classification Output
    document_type: str
    classification_confidence: float
    classification_details: Dict[str, Any]

    # Agent 4: Extraction Output
    extracted_data: Dict[str, Any]
    line_items: List[Dict[str, Any]]
    field_confidences: Dict[str, float]

    # Agent 5: Validation Output
    validation_status: str  # PASSED, WARNING, FAILED
    is_valid: bool
    validation_errors: List[Dict[str, Any]]
    validation_warnings: List[Dict[str, Any]]
    validation_explanations: Dict[str, Any]

    # Agent 6: Duplicate Detection Output
    duplicate_matches: List[Dict[str, Any]]

    # Agent 7: Anomaly Detection Output
    anomaly_findings: List[Dict[str, Any]]

    # Agent 8: Decision & Approval
    decision: str  # APPROVED_FOR_REVIEW, NEEDS_HUMAN_REVIEW, REJECTED, PROCESSING_FAILED
    approval_status: str
    assigned_reviewer_id: Optional[str]

    # Agent 9: Reporting & Finalization
    finalized: bool
    invoice_id: Optional[str]

    # Workflow Metadata & Metrics
    agent_executions: List[Dict[str, Any]]
    current_step: str
    error: Optional[str]
