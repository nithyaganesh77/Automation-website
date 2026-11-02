from app.models.all_models import Organization, User, OrganizationMember, Document
from app.core.security import hash_password, create_access_token


def test_tenant_isolation(client, db_session, test_org_and_admin):
    # Create Organization B
    org_b = Organization(name="Organization B", slug="org-b")
    db_session.add(org_b)
    db_session.flush()

    user_b = User(
        email="user_b@orgb.com",
        hashed_password=hash_password("Pass123!"),
        full_name="User B",
        is_active=True,
        is_superuser=False
    )
    db_session.add(user_b)
    db_session.flush()

    db_session.add(OrganizationMember(organization_id=org_b.id, user_id=user_b.id, role="Admin"))
    
    # Document belonging to Organization B
    doc_b = Document(
        organization_id=org_b.id,
        user_id=user_b.id,
        file_name="secret_b_invoice.pdf",
        file_path="/tmp/secret_b.pdf",
        file_size=1024,
        mime_type="application/pdf",
        file_hash_sha256="abc123456789",
        status="APPROVED"
    )
    db_session.add(doc_b)
    db_session.commit()

    # User from Organization A attempts to access Document B
    token_a = test_org_and_admin["token"]
    headers = {"Authorization": f"Bearer {token_a}"}

    # Should return 404 (Document not found in tenant's partition)
    response = client.get(f"/api/v1/documents/{doc_b.id}", headers=headers)
    assert response.status_code == 404

    # Organization A document list must NOT contain Document B
    list_response = client.get("/api/v1/documents", headers=headers)
    assert list_response.status_code == 200
    doc_ids = [d["id"] for d in list_response.json()["items"]]
    assert doc_b.id not in doc_ids

