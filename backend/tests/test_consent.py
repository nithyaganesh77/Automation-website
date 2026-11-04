import pytest
from pathlib import Path
from app.models.all_models import Document, Invoice, AuditLog, AgentExecution

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SYNTHETIC_PDF_PATH = ROOT_DIR / "evaluation" / "datasets" / "phase2" / "p2_invoice_01_clean_intra.pdf"


def test_upload_missing_consent_rejected_422(client, test_org_and_admin, db_session):
    """A. Upload without customer_consent field must return HTTP 422 (Unprocessable Entity)."""
    token = test_org_and_admin["token"]
    org = test_org_and_admin["org"]
    headers = {"Authorization": f"Bearer {token}"}

    docs_before = db_session.query(Document).filter(Document.organization_id == org.id).count()
    invs_before = db_session.query(Invoice).filter(Invoice.organization_id == org.id).count()
    audits_before = db_session.query(AuditLog).filter(
        AuditLog.organization_id == org.id,
        AuditLog.action == "DOCUMENT_UPLOADED"
    ).count()

    with open(SYNTHETIC_PDF_PATH, "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": ("test_missing_consent.pdf", f.read(), "application/pdf")}
            # Note: customer_consent omitted entirely
        )

    # Must be rejected at validation boundary
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

    # Verify no database records, invoices, or audit logs created
    docs_after = db_session.query(Document).filter(Document.organization_id == org.id).count()
    invs_after = db_session.query(Invoice).filter(Invoice.organization_id == org.id).count()
    audits_after = db_session.query(AuditLog).filter(
        AuditLog.organization_id == org.id,
        AuditLog.action == "DOCUMENT_UPLOADED"
    ).count()

    assert docs_after == docs_before, "Document record was created despite missing consent!"
    assert invs_after == invs_before, "Invoice record was created despite missing consent!"
    assert audits_after == audits_before, "Ingestion audit log was recorded despite missing consent!"


def test_upload_false_consent_rejected_400(client, test_org_and_admin, db_session):
    """B. Upload with customer_consent=false must be explicitly rejected with HTTP 400."""
    token = test_org_and_admin["token"]
    org = test_org_and_admin["org"]
    headers = {"Authorization": f"Bearer {token}"}

    docs_before = db_session.query(Document).filter(Document.organization_id == org.id).count()
    invs_before = db_session.query(Invoice).filter(Invoice.organization_id == org.id).count()
    agents_before = db_session.query(AgentExecution).count()

    with open(SYNTHETIC_PDF_PATH, "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": ("test_false_consent.pdf", f.read(), "application/pdf")},
            data={"customer_consent": "false"}
        )

    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["detail"] == "Document upload requires explicit customer consent."

    # Verify D: Rejected upload does not create documents, invoices, OCR/agents
    docs_after = db_session.query(Document).filter(Document.organization_id == org.id).count()
    invs_after = db_session.query(Invoice).filter(Invoice.organization_id == org.id).count()
    agents_after = db_session.query(AgentExecution).count()

    assert docs_after == docs_before, "Document record was created on false consent!"
    assert invs_after == invs_before, "Invoice record was created on false consent!"
    assert agents_after == agents_before, "Agent execution was initiated on false consent!"


def test_upload_true_consent_allowed_and_audited(client, test_org_and_admin, db_session):
    """C & E. Upload with customer_consent=true executes workflow and records affirmative consent in audit log."""
    token = test_org_and_admin["token"]
    org = test_org_and_admin["org"]
    headers = {"Authorization": f"Bearer {token}"}

    with open(SYNTHETIC_PDF_PATH, "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": ("test_valid_consent.pdf", f.read(), "application/pdf")},
            data={"customer_consent": "true"}
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    doc_data = response.json()
    doc_id = doc_data["id"]
    assert doc_id is not None

    # Verify audit log recorded affirmative consent
    audit = db_session.query(AuditLog).filter(
        AuditLog.organization_id == org.id,
        AuditLog.entity_id == doc_id,
        AuditLog.action == "DOCUMENT_UPLOADED"
    ).first()

    assert audit is not None, "Audit log was not created for valid document upload!"
    assert audit.details.get("consent_obtained") is True, f"Audit log did not record consent_obtained=True: {audit.details}"

