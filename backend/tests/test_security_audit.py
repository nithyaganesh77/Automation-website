import io
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
import jwt

from app.models.all_models import (
    User, Organization, OrganizationMember, Document, Invoice
)
from app.core.security import hash_password, create_access_token
from app.core.config import settings
from tests.conftest import TestingSessionLocal


@pytest.fixture
def sec_fixtures(db_session, monkeypatch):
    monkeypatch.setattr("app.agents.nodes.SessionLocal", TestingSessionLocal)

    uid = uuid.uuid4().hex[:6]
    org1_id = f"sec-org1-{uid}"
    org2_id = f"sec-org2-{uid}"

    # Tenant 1
    org1 = Organization(id=org1_id, name="Security Alpha", slug=f"sec-alpha-{uid}")
    db_session.add(org1)
    
    u1_admin_id = f"sec-u1-adm-{uid}"
    u1_admin = User(
        id=u1_admin_id,
        email=f"admin_{uid}@sec-alpha.com",
        full_name="Alpha Admin",
        hashed_password=hash_password("SecPass123!@#")
    )
    db_session.add(u1_admin)
    db_session.add(OrganizationMember(id=f"mem1-{uid}", organization_id=org1_id, user_id=u1_admin_id, role="Admin"))

    u1_view_id = f"sec-u1-view-{uid}"
    u1_view = User(
        id=u1_view_id,
        email=f"viewer_{uid}@sec-alpha.com",
        full_name="Alpha Viewer",
        hashed_password=hash_password("SecPass123!@#")
    )
    db_session.add(u1_view)
    db_session.add(OrganizationMember(id=f"mem2-{uid}", organization_id=org1_id, user_id=u1_view_id, role="Viewer"))

    # Tenant 2
    org2 = Organization(id=org2_id, name="Security Beta", slug=f"sec-beta-{uid}")
    db_session.add(org2)
    u2_admin_id = f"sec-u2-adm-{uid}"
    u2_admin = User(
        id=u2_admin_id,
        email=f"admin_{uid}@sec-beta.com",
        full_name="Beta Admin",
        hashed_password=hash_password("SecPass123!@#")
    )
    db_session.add(u2_admin)
    db_session.add(OrganizationMember(id=f"mem3-{uid}", organization_id=org2_id, user_id=u2_admin_id, role="Admin"))

    # Seed Document in Tenant 1
    doc1 = Document(
        id=f"sec-doc1-{uid}",
        organization_id=org1_id,
        file_name="confidential_contract.pdf",
        file_path="/tmp/confidential_contract.pdf",
        file_size=1024,
        mime_type="application/pdf",
        file_hash_sha256=f"hash_sec_{uid}",
        status="PROCESSED"
    )
    db_session.add(doc1)
    db_session.commit()

    token_t1_admin = create_access_token(u1_admin_id, org1_id, "Admin")
    token_t1_view = create_access_token(u1_view_id, org1_id, "Viewer")
    token_t2_admin = create_access_token(u2_admin_id, org2_id, "Admin")

    return {
        "headers_t1_admin": {"Authorization": f"Bearer {token_t1_admin}"},
        "headers_t1_view": {"Authorization": f"Bearer {token_t1_view}"},
        "headers_t2_admin": {"Authorization": f"Bearer {token_t2_admin}"},
        "doc1_id": f"sec-doc1-{uid}",
        "org1_id": org1_id,
        "org2_id": org2_id
    }


def test_security_response_headers(client):
    """Verify standard defensive HTTP headers are attached to API responses."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_path_traversal_and_filename_sanitization(client, sec_fixtures, monkeypatch):
    """
    Verify that filenames containing directory traversal (e.g., ../../evil.pdf)
    are strictly sanitized and contained within the tenant storage path.
    """
    monkeypatch.setattr(settings, "DISABLE_EXTERNAL_AI", True)
    headers = sec_fixtures["headers_t1_admin"]
    fake_pdf = b"%PDF-1.4 Minimal test pdf content"

    res = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("../../../../etc/passwd.pdf", fake_pdf, "application/pdf")},
        data={"customer_consent": "true"}
    )
    # Upload succeeds only with sanitized, non-traversing filename
    assert res.status_code == 200
    doc = res.json()
    assert ".." not in doc["file_name"]
    assert "/" not in doc["file_name"]
    assert "\\" not in doc["file_name"]


def test_disallowed_file_extensions_rejected(client, sec_fixtures):
    """Verify unauthorized executable/script extensions are blocked with 400 Bad Request."""
    headers = sec_fixtures["headers_t1_admin"]
    dangerous_payload = b"echo 'malicious script'"

    for dangerous_ext in ["payload.exe", "backdoor.sh", "exploit.php", "script.bat"]:
        res = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": (dangerous_ext, dangerous_payload, "application/octet-stream")},
            data={"customer_consent": "true"}
        )
        assert res.status_code == 400
        assert "Unsupported file extension" in res.json()["detail"]


def test_cross_tenant_document_leakage(client, sec_fixtures):
    """
    Verify that Tenant 2 cannot access, read, or modify Document 1 belonging to Tenant 1.
    """
    doc1_id = sec_fixtures["doc1_id"]
    headers_t2 = sec_fixtures["headers_t2_admin"]

    # Tenant 2 attempts to get Tenant 1 document
    res = client.get(f"/api/v1/documents/{doc1_id}", headers=headers_t2)
    assert res.status_code in [404, 403]


def test_sql_injection_defense_in_parameters(client, sec_fixtures):
    """
    Verify that SQL injection payloads in query filters are safely parameterized.
    """
    headers = sec_fixtures["headers_t1_admin"]
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE documents; --",
        "1 UNION SELECT 1,2,3,4,5"
    ]

    for sqli in sqli_payloads:
        res = client.get(f"/api/v1/documents?search={sqli}", headers=headers)
        # Must return valid 200 with 0 results or 422, never a 500 database execution crash
        assert res.status_code in [200, 422]
        if res.status_code == 200:
            data = res.json()
            assert "items" in data
            assert isinstance(data["items"], list)


def test_jwt_tampering_and_forgery_rejected(client, sec_fixtures):
    """Verify that manipulated JWT tokens or wrong signing keys are rejected with 401."""
    # 1. Tampered signature
    headers_tampered = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.FAKESIGNATURE"}
    res = client.get("/api/v1/compliance/consent/status", headers=headers_tampered)
    assert res.status_code == 401

    # 2. Token signed with wrong secret key
    forged_token = jwt.encode(
        {"sub": "attacker", "org_id": "sec-org1", "role": "Admin", "type": "access"},
        "wrong_secret_key_12345",
        algorithm="HS256"
    )
    res = client.get("/api/v1/compliance/consent/status", headers={"Authorization": f"Bearer {forged_token}"})
    assert res.status_code == 401

    # 3. Expired token
    expired_token = jwt.encode(
        {
            "sub": "expired_user",
            "org_id": "sec-org1",
            "role": "Admin",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    res = client.get("/api/v1/compliance/consent/status", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401


def test_rbac_authorization_boundaries(client, sec_fixtures):
    """Verify that Viewer roles cannot execute privileged administrative endpoints."""
    headers_viewer = sec_fixtures["headers_t1_view"]

    # Viewer tries to withdraw consent -> 403 Forbidden
    res = client.post(
        "/api/v1/compliance/consent/withdraw",
        headers=headers_viewer,
        json={"reason": "Unauthorized attempt"}
    )
    assert res.status_code == 403

    # Viewer tries to update retention policy -> 403 Forbidden
    res = client.patch(
        "/api/v1/compliance/retention-policy",
        headers=headers_viewer,
        json={"retention_policy_days": 90}
    )
    assert res.status_code == 403

    # Viewer tries to update organizational settings -> 403 Forbidden
    res = client.patch(
        "/api/v1/settings",
        headers=headers_viewer,
        json={"currency": "USD"}
    )
    assert res.status_code == 403
