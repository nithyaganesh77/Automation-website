import os
import io
import pytest
from app.models.all_models import Document, ExportRecord, User, Organization, OrganizationMember
from app.core.security import create_access_token


def test_unauthenticated_protected_endpoints_return_401(client):
    """Verify accessing protected endpoints without a Bearer token returns HTTP 401."""
    endpoints = [
        "/api/v1/documents",
        "/api/v1/invoices",
        "/api/v1/reports/dashboard",
        "/api/v1/suppliers",
        "/api/v1/approvals"
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 401, f"Expected 401 for unauthenticated request to {ep}, got {resp.status_code}"


def test_disguised_executable_rejected(client, test_org_and_admin):
    """Verify that uploading a disguised .exe renamed to .pdf fails magic bytes validation."""
    token = test_org_and_admin["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Disguised Windows PE Executable starting with 'MZ' magic bytes
    fake_exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00This program cannot be run in DOS mode."
    files = {"file": ("malicious_invoice.pdf", io.BytesIO(fake_exe_bytes), "application/pdf")}
    data = {"customer_consent": "true"}

    response = client.post("/api/v1/documents/upload", headers=headers, files=files, data=data)
    assert response.status_code == 400
    assert "Executable" in response.json().get("detail", "") or "rejected" in response.json().get("detail", "")


def test_path_traversal_sanitized_to_safe_uuid(client, test_org_and_admin, db_session):
    """Verify that filenames containing path traversal patterns (../../etc/passwd) are sanitized to safe UUIDs."""
    token = test_org_and_admin["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Genuine PDF content
    genuine_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
    traversal_filename = "../../../../etc/passwd.pdf"
    files = {"file": (traversal_filename, io.BytesIO(genuine_pdf_bytes), "application/pdf")}
    data = {"customer_consent": "true"}

    response = client.post("/api/v1/documents/upload", headers=headers, files=files, data=data)
    assert response.status_code == 200
    doc_data = response.json()

    # Verify metadata filename does not contain path traversal indicators
    assert ".." not in doc_data["file_name"]
    assert "/" not in doc_data["file_name"]
    assert "\\" not in doc_data["file_name"]

    # Verify physical file stored on disk is named with a random UUID
    db_doc = db_session.query(Document).filter(Document.id == doc_data["id"]).first()
    assert db_doc is not None
    stored_basename = os.path.basename(db_doc.file_path)
    # Stored filename must be {uuid4()}.pdf
    assert stored_basename.endswith(".pdf")
    assert "passwd" not in stored_basename
    assert ".." not in db_doc.file_path


def test_rate_limiting_login_threshold(client):
    """Verify that exceeding login attempts triggers HTTP 429 Too Many Requests."""
    bad_login = {
        "email": "rate_limit_target@documind.ai",
        "password": "WrongPasswordAttempt!"
    }
    
    # 5 attempts allowed per 15 minutes, 6th attempt should be blocked with 429
    responses = []
    for _ in range(6):
        res = client.post("/api/v1/auth/login", json=bad_login)
        responses.append(res.status_code)

    assert 429 in responses, f"Expected HTTP 429 in responses, got {responses}"


def test_export_signed_download_token_single_use(client, test_org_and_admin, db_session):
    """Verify single-use cryptographically signed download tokens for export downloads."""
    org = test_org_and_admin["org"]
    admin = test_org_and_admin["user"]
    token = test_org_and_admin["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure export directory exists
    export_dir = os.path.join("storage", "exports", org.id)
    os.makedirs(export_dir, exist_ok=True)
    dummy_csv_path = os.path.join(export_dir, "test_export.csv")
    with open(dummy_csv_path, "w") as f:
        f.write("invoice_number,total\nINV-001,1000\n")

    export_rec = ExportRecord(
        organization_id=org.id,
        user_id=admin.id,
        export_type="INVOICES",
        format="CSV",
        file_path=dummy_csv_path,
        record_count=1
    )
    db_session.add(export_rec)
    db_session.commit()
    db_session.refresh(export_rec)

    # 1. Generate 60-second signed single-use download token
    token_resp = client.post(f"/api/v1/reports/exports/{export_rec.id}/token", headers=headers)
    assert token_resp.status_code == 200
    token_data = token_resp.json()
    assert "download_token" in token_data
    download_token = token_data["download_token"]

    # 2. First download request succeeds (without Bearer header, only ?token=...)
    dl_resp1 = client.get(f"/api/v1/reports/exports/{export_rec.id}/download?token={download_token}")
    assert dl_resp1.status_code == 200
    assert "INV-001" in dl_resp1.text

    # 3. Second download request with the same token MUST fail (Single-Use Token Burned)
    dl_resp2 = client.get(f"/api/v1/reports/exports/{export_rec.id}/download?token={download_token}")
    assert dl_resp2.status_code == 401
    assert "consumed" in dl_resp2.json().get("detail", "").lower()
