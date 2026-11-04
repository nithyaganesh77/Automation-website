import io
import socket
import uuid
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient

from app.models.all_models import (
    User, Organization, OrganizationMember, OrganizationSetting,
    Document, Invoice, InvoiceLineItem, Supplier, AuditLog, DataRightsRequest
)
from app.core.security import hash_password, create_access_token
from app.core.config import settings
from tests.conftest import TestingSessionLocal


@pytest.fixture
def org_fixtures(db_session, monkeypatch):
    monkeypatch.setattr("app.agents.nodes.SessionLocal", TestingSessionLocal)

    uid = uuid.uuid4().hex[:6]
    org1_id = f"org-c1-{uid}"
    org2_id = f"org-c2-{uid}"

    # Org 1
    org1 = Organization(id=org1_id, name=f"Alpha Logistics {uid}", slug=f"alpha-logistics-{uid}")
    db_session.add(org1)
    
    user1_id = f"user-c1-admin-{uid}"
    user1 = User(
        id=user1_id,
        email=f"admin_{uid}@alpha.com",
        full_name="Alpha Admin",
        hashed_password=hash_password("SecretPassword123!")
    )
    db_session.add(user1)
    
    mem1 = OrganizationMember(
        id=f"mem-c1-{uid}",
        organization_id=org1_id,
        user_id=user1_id,
        role="Admin"
    )
    db_session.add(mem1)

    user1_rev_id = f"user-c1-rev-{uid}"
    user1_rev = User(
        id=user1_rev_id,
        email=f"reviewer_{uid}@alpha.com",
        full_name="Alpha Reviewer",
        hashed_password=hash_password("SecretPassword123!")
    )
    db_session.add(user1_rev)
    
    mem1_rev = OrganizationMember(
        id=f"mem-c1-rev-{uid}",
        organization_id=org1_id,
        user_id=user1_rev_id,
        role="Reviewer"
    )
    db_session.add(mem1_rev)
    
    setting1 = OrganizationSetting(
        id=f"set-c1-{uid}",
        organization_id=org1_id,
        ai_provider="gemini",
        primary_provider="gemini",
        fallback_provider="groq",
        tenant_disable_external_ai=False,
        consent_withdrawn=False,
        retention_policy_days=365
    )
    db_session.add(setting1)

    # Org 2 (for tenant boundary testing)
    org2 = Organization(id=org2_id, name=f"Beta Solutions {uid}", slug=f"beta-solutions-{uid}")
    db_session.add(org2)
    
    user2_id = f"user-c2-admin-{uid}"
    user2 = User(
        id=user2_id,
        email=f"admin_{uid}@beta.com",
        full_name="Beta Admin",
        hashed_password=hash_password("SecretPassword123!")
    )
    db_session.add(user2)
    
    mem2 = OrganizationMember(
        id=f"mem-c2-{uid}",
        organization_id=org2_id,
        user_id=user2_id,
        role="Admin"
    )
    db_session.add(mem2)
    
    setting2 = OrganizationSetting(
        id=f"set-c2-{uid}",
        organization_id=org2_id,
        ai_provider="gemini",
        tenant_disable_external_ai=False,
        consent_withdrawn=False
    )
    db_session.add(setting2)

    db_session.commit()

    token_org1_admin = create_access_token(user1_id, org1_id, "Admin")
    token_org1_rev = create_access_token(user1_rev_id, org1_id, "Reviewer")
    token_org2_admin = create_access_token(user2_id, org2_id, "Admin")

    return {
        "headers_org1": {"Authorization": f"Bearer {token_org1_admin}"},
        "headers_org1_rev": {"Authorization": f"Bearer {token_org1_rev}"},
        "headers_org2": {"Authorization": f"Bearer {token_org2_admin}"},
        "org1_id": org1_id,
        "org2_id": org2_id,
        "user1_id": user1_id,
        "uid": uid
    }


def test_consent_withdrawal_and_re_grant(client, db_session, org_fixtures):
    headers = org_fixtures["headers_org1"]
    org1_id = org_fixtures["org1_id"]

    # 1. Check initial consent status
    res = client.get("/api/v1/compliance/consent/status", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["consent_withdrawn"] is False
    assert data["organization_id"] == org1_id

    # 2. Withdraw consent
    res = client.post(
        "/api/v1/compliance/consent/withdraw",
        headers=headers,
        json={"reason": "Customer opted out of cloud AI processing under DPDP"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["consent_withdrawn"] is True
    assert data["effective_external_ai_disabled"] is True
    assert data["consent_withdrawn_at"] is not None

    # Verify DataRightsRequest logged
    req = db_session.query(DataRightsRequest).filter(
        DataRightsRequest.organization_id == org1_id,
        DataRightsRequest.request_type == "CONSENT_WITHDRAWAL"
    ).first()
    assert req is not None
    assert req.status == "COMPLETED"

    # Verify AuditLog event logged
    audit = db_session.query(AuditLog).filter(
        AuditLog.organization_id == org1_id,
        AuditLog.action == "CUSTOMER_CONSENT_WITHDRAWN"
    ).first()
    assert audit is not None
    assert audit.details["historical_documents_preserved"] is True

    # 3. Re-grant consent
    res = client.post(
        "/api/v1/compliance/consent/grant",
        headers=headers,
        json={"notes": "Customer agreed to renewed data terms"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["consent_withdrawn"] is False


def test_prevention_of_external_ai_after_consent_withdrawal(client, db_session, org_fixtures, monkeypatch):
    """
    Empirically prove that when a tenant has withdrawn consent,
    document uploads execute locally with zero external network socket calls.
    """
    headers = org_fixtures["headers_org1"]

    # Withdraw consent for org
    client.post(
        "/api/v1/compliance/consent/withdraw",
        headers=headers,
        json={"reason": "Revoked consent test"}
    )

    # Block socket connections at OS level
    def fail_on_connect(*args, **kwargs):
        raise AssertionError("Network socket connection attempted when tenant consent is withdrawn!")

    monkeypatch.setattr(socket.socket, "connect", fail_on_connect)

    from pathlib import Path
    repo_root = Path(__file__).resolve().parent.parent.parent
    synthetic_pdf = repo_root / "evaluation" / "datasets" / "phase2" / "p2_invoice_01_clean_intra.pdf"

    with open(synthetic_pdf, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("airgap_invoice.pdf", file_bytes, "application/pdf")},
        data={"customer_consent": "true"}
    )

    assert response.status_code == 200
    doc_data = response.json()
    assert doc_data["status"] in ["PROCESSED", "NEEDS_REVIEW", "PENDING_APPROVAL"]
    doc_id = doc_data["id"]

    # Verify document in DB has zero external AI token/cost footprint
    doc_in_db = db_session.query(Document).filter(Document.id == doc_id).first()
    assert doc_in_db is not None
    assert doc_in_db.file_name == "airgap_invoice.pdf"
    assert doc_in_db.extracted_tokens == 0
    assert float(doc_in_db.estimated_cost_usd) == 0.0


def test_global_privacy_mode_cannot_be_bypassed_by_tenant(client, db_session, org_fixtures, monkeypatch):
    """
    Guarantee that if global DISABLE_EXTERNAL_AI is True,
    no tenant-level settings (granting consent or toggling preferences) can enable external AI.
    """
    monkeypatch.setattr(settings, "DISABLE_EXTERNAL_AI", True)
    headers = org_fixtures["headers_org1"]

    # Tenant attempts to set tenant_disable_external_ai to False
    res = client.patch(
        "/api/v1/compliance/preferences",
        headers=headers,
        json={"tenant_disable_external_ai": False}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["tenant_disable_external_ai"] is False
    assert data["global_privacy_mode_active"] is True
    # Effective status MUST remain True
    assert data["effective_external_ai_disabled"] is True


def test_tenant_data_export_and_isolation(client, db_session, org_fixtures):
    headers1 = org_fixtures["headers_org1"]
    org1_id = org_fixtures["org1_id"]
    org2_id = org_fixtures["org2_id"]
    uid = org_fixtures["uid"]

    # Seed an invoice in org-1
    inv1 = Invoice(
        id=f"inv-c1-{uid}",
        document_id=f"doc-c1-{uid}",
        organization_id=org1_id,
        invoice_number=f"INV-ORG1-{uid}",
        invoice_date="2026-11-01",
        supplier_name_raw="Supplier One",
        subtotal=Decimal("1000.00"),
        total_tax=Decimal("180.00"),
        grand_total=Decimal("1180.00"),
        status="APPROVED"
    )
    db_session.add(inv1)

    # Seed an invoice in org-2
    inv2 = Invoice(
        id=f"inv-c2-{uid}",
        document_id=f"doc-c2-{uid}",
        organization_id=org2_id,
        invoice_number=f"INV-ORG2-{uid}",
        invoice_date="2026-11-01",
        supplier_name_raw="Secret Competitor",
        subtotal=Decimal("50000.00"),
        total_tax=Decimal("9000.00"),
        grand_total=Decimal("59000.00"),
        status="APPROVED"
    )
    db_session.add(inv2)
    db_session.commit()

    # Request export for org-1
    res = client.post(
        "/api/v1/compliance/export",
        headers=headers1,
        json={"export_type": "ALL", "format": "JSON"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_invoices"] == 1
    export_invoices = data["data"]["invoices"]
    assert len(export_invoices) == 1
    assert export_invoices[0]["invoice_number"] == f"INV-ORG1-{uid}"
    # Verify Tenant Isolation: org-2 invoice MUST NOT appear
    assert f"INV-ORG2-{uid}" not in str(data)


def test_data_deletion_lifecycle_and_boundary(client, db_session, org_fixtures):
    headers1 = org_fixtures["headers_org1"]
    headers2 = org_fixtures["headers_org2"]
    org1_id = org_fixtures["org1_id"]
    org2_id = org_fixtures["org2_id"]
    uid = org_fixtures["uid"]

    doc1_id = f"doc-del-c1-{uid}"
    doc2_id = f"doc-keep-c2-{uid}"

    # Seed documents for org-1 and org-2
    doc1 = Document(
        id=doc1_id, organization_id=org1_id, file_name="bill.pdf",
        file_path="/tmp/bill.pdf", file_size=100, mime_type="application/pdf",
        file_hash_sha256=f"hash1_{uid}", status="PROCESSED"
    )
    doc2 = Document(
        id=doc2_id, organization_id=org2_id, file_name="beta_bill.pdf",
        file_path="/tmp/beta_bill.pdf", file_size=200, mime_type="application/pdf",
        file_hash_sha256=f"hash2_{uid}", status="PROCESSED"
    )
    db_session.add_all([doc1, doc2])
    db_session.commit()

    # 1. Invalid confirmation phrase should be rejected
    res = client.post(
        "/api/v1/compliance/deletion-request",
        headers=headers1,
        json={"reason": "Customer offboarding", "confirm_phrase": "WRONG PHRASE"}
    )
    assert res.status_code == 400

    # 2. Correct confirmation phrase creates pending request
    res = client.post(
        "/api/v1/compliance/deletion-request",
        headers=headers1,
        json={"reason": "Customer offboarding", "confirm_phrase": "DELETE ALL TENANT DATA"}
    )
    assert res.status_code == 200
    req_id = res.json()["id"]

    # 3. Cross-tenant execution attempt (org-2 tries to execute org-1's deletion) -> 404
    res = client.post(
        f"/api/v1/compliance/deletion-request/{req_id}/execute",
        headers=headers2
    )
    assert res.status_code == 404

    # 4. Valid execution by org-1 Admin
    res = client.post(
        f"/api/v1/compliance/deletion-request/{req_id}/execute",
        headers=headers1
    )
    assert res.status_code == 200
    del_data = res.json()
    assert del_data["status"] == "COMPLETED"
    assert del_data["records_purged"]["documents"] == 1

    # Verify org-1 document is gone, but org-2 document is intact!
    assert db_session.query(Document).filter(Document.id == doc1_id).first() is None
    assert db_session.query(Document).filter(Document.id == doc2_id).first() is not None


def test_retention_policy_management(client, db_session, org_fixtures):
    headers1 = org_fixtures["headers_org1"]
    headers1_rev = org_fixtures["headers_org1_rev"]

    # 1. Get retention policy
    res = client.get("/api/v1/compliance/retention-policy", headers=headers1)
    assert res.status_code == 200
    assert res.json()["retention_policy_days"] == 365

    # 2. Reviewer role cannot update retention policy (403 Forbidden)
    res = client.patch(
        "/api/v1/compliance/retention-policy",
        headers=headers1_rev,
        json={"retention_policy_days": 180}
    )
    assert res.status_code == 403

    # 3. Invalid days (< 30) rejected
    res = client.patch(
        "/api/v1/compliance/retention-policy",
        headers=headers1,
        json={"retention_policy_days": 10}
    )
    assert res.status_code == 400

    # 4. Admin updates retention policy
    res = client.patch(
        "/api/v1/compliance/retention-policy",
        headers=headers1,
        json={"retention_policy_days": 180}
    )
    assert res.status_code == 200
    assert res.json()["retention_policy_days"] == 180
