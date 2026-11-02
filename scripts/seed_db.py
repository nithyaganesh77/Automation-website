import os
import shutil
from datetime import datetime, timezone
from decimal import Decimal
from app.database.session import SessionLocal, Base, engine
from app.models.all_models import (
    Organization, User, Role, Permission, OrganizationMember, OrganizationSetting,
    Supplier, Document
)
from app.core.security import hash_password
from app.agents.graph import execute_document_workflow
from app.agents.state import DocuMindState
from app.services.storage import StorageService
from app.core.config import settings

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Organization
        org = db.query(Organization).filter(Organization.slug == "documind-enterprise").first()
        if not org:
            org = Organization(name="DocuMind Enterprise Corp", slug="documind-enterprise")
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Created Organization: {org.name} ({org.id})")

        # 2. Organization Settings
        setting = db.query(OrganizationSetting).filter(OrganizationSetting.organization_id == org.id).first()
        if not setting:
            setting = OrganizationSetting(
                organization_id=org.id,
                ai_provider="gemini",
                confidence_threshold=0.85,
                tax_tolerance=2.00,
                auto_approve_threshold=0.98,
                currency="INR"
            )
            db.add(setting)
            db.commit()

        # 3. Users
        admin_user = db.query(User).filter(User.email == "admin@documind.ai").first()
        if not admin_user:
            admin_user = User(
                email="admin@documind.ai",
                hashed_password=hash_password("Password123!"),
                full_name="Alex Mercer (Chief Admin)",
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            db.add(OrganizationMember(
                organization_id=org.id,
                user_id=admin_user.id,
                role="Admin"
            ))
            db.commit()
            print("Created Admin user: admin@documind.ai / Password123!")

        reviewer_user = db.query(User).filter(User.email == "reviewer@documind.ai").first()
        if not reviewer_user:
            reviewer_user = User(
                email="reviewer@documind.ai",
                hashed_password=hash_password("Password123!"),
                full_name="Sarah Jenkins (Senior Financial Reviewer)",
                is_active=True,
                is_superuser=False
            )
            db.add(reviewer_user)
            db.commit()
            db.refresh(reviewer_user)

            db.add(OrganizationMember(
                organization_id=org.id,
                user_id=reviewer_user.id,
                role="Reviewer"
            ))
            db.commit()
            print("Created Reviewer user: reviewer@documind.ai / Password123!")

        # 4. Suppliers
        suppliers_data = [
            {
                "name": "Apex Cloud Technologies Pvt Ltd",
                "gstin": "29ABCDE1234F1Z5",
                "pan": "ABCDE1234F",
                "address": "42 Tech Park, Outer Ring Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560103",
                "total_spend": Decimal("236000.00"),
                "invoice_count": 2
            },
            {
                "name": "CyberShield Security Systems Ltd",
                "gstin": "27AABCC9988D1Z9",
                "pan": "AABCC9988D",
                "address": "88 Nariman Point",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400021",
                "total_spend": Decimal("88500.00"),
                "invoice_count": 1
            },
            {
                "name": "Metro Office Spaces & Coworking",
                "gstin": "29BBBBB4433P1Z1",
                "pan": "BBBBB4433P",
                "address": "77 MG Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560001",
                "total_spend": Decimal("9440.00"),
                "invoice_count": 1
            }
        ]

        for s_data in suppliers_data:
            s_exist = db.query(Supplier).filter(Supplier.organization_id == org.id, Supplier.name == s_data["name"]).first()
            if not s_exist:
                supp = Supplier(organization_id=org.id, **s_data)
                db.add(supp)
        db.commit()
        print("Suppliers seeded successfully.")

        # 5. Process synthetic documents through LangGraph
        dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evaluation", "datasets")
        sample_files = [
            "invoice_standard_01.pdf",
            "invoice_standard_02.pdf",
            "invoice_math_error.pdf",
            "invoice_duplicate.pdf",
            "purchase_order_01.pdf",
            "receipt_01.pdf"
        ]

        for filename in sample_files:
            src_path = os.path.join(dataset_dir, filename)
            if not os.path.exists(src_path):
                continue

            file_hash = StorageService.compute_sha256(src_path)
            file_size = os.path.getsize(src_path)

            # Copy to storage
            org_dir = os.path.join(settings.UPLOAD_DIR, org.id)
            os.makedirs(org_dir, exist_ok=True)
            dest_path = os.path.join(org_dir, filename)
            shutil.copy2(src_path, dest_path)

            # Check if already processed
            existing_doc = db.query(Document).filter(
                Document.organization_id == org.id,
                Document.file_name == filename
            ).first()

            if not existing_doc:
                doc = Document(
                    organization_id=org.id,
                    user_id=admin_user.id,
                    file_name=filename,
                    file_path=dest_path,
                    file_size=file_size,
                    mime_type="application/pdf",
                    file_hash_sha256=file_hash,
                    status="PROCESSING"
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)

                # Run multi-agent pipeline
                state = DocuMindState(
                    document_id=doc.id,
                    organization_id=org.id,
                    user_id=admin_user.id,
                    file_path=doc.file_path,
                    file_name=doc.file_name,
                    file_hash=doc.file_hash_sha256,
                    mime_type=doc.mime_type,
                    file_size=doc.file_size
                )
                print(f"Executing LangGraph pipeline for {filename}...")
                execute_document_workflow(state)

        print("Database seed & synthetic document processing finished successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
