from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ValidationErrorItem(BaseModel):
    field: str
    message: str
    code: str
    expected: Optional[str] = None
    actual: Optional[str] = None


class ValidationWarningItem(BaseModel):
    field: str
    message: str
    code: str


class ValidationResultOut(BaseModel):
    id: str
    document_id: str
    invoice_id: Optional[str] = None
    status: str  # PASSED, WARNING, FAILED
    is_valid: bool
    errors: List[ValidationErrorItem] = []
    warnings: List[ValidationWarningItem] = []
    field_explanations: Dict[str, Any] = {}

    class Config:
        from_attributes = True

