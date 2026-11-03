import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Numeric, JSON
)
from sqlalchemy.orm import relationship
from app.database.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    legal_name = Column(String(255), nullable=True)
    gstin = Column(String(15), nullable=True)
    pan = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_step = Column(String(50), default="PROFILE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="organization", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="organization", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="organization", cascade="all, delete-orphan")
    settings = relationship("OrganizationSetting", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    invitations = relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="Admin", nullable=False)  # Admin, Reviewer, Viewer, Operator
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False, index=True)
    status = Column(String(50), default="UPLOADED", nullable=False, index=True)
    document_type = Column(String(50), default="Other", nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    extracted_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Numeric(10, 6), default=Decimal("0.000000"), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="document", uselist=False, cascade="all, delete-orphan")
    validations = relationship("ValidationResult", back_populates="document", cascade="all, delete-orphan")
    duplicates = relationship("DuplicateMatch", foreign_keys="DuplicateMatch.document_id", back_populates="document", cascade="all, delete-orphan")
    anomalies = relationship("AnomalyFinding", back_populates="document", cascade="all, delete-orphan")
    agent_executions = relationship("AgentExecution", back_populates="document", cascade="all, delete-orphan")
    approval_request = relationship("ApprovalRequest", back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=False)
    ocr_engine = Column(String(50), default="native_pdf", nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    page_metadata = Column(JSON, nullable=True)

    document = relationship("Document", back_populates="pages")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    field_value = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0, nullable=False)
    source_page = Column(Integer, default=1, nullable=False)
    evidence_text = Column(Text, nullable=True)
    is_corrected = Column(Boolean, default=False, nullable=False)
    corrected_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="extracted_fields")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    gstin = Column(String(15), nullable=True, index=True)
    pan = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="India", nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    total_spend = Column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    invoice_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="suppliers")
    invoices = relationship("Invoice", back_populates="supplier")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15), nullable=True)
    address = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    po_number = Column(String(100), nullable=False, index=True)
    po_date = Column(String(50), nullable=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    status = Column(String(50), default="OPEN", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    invoice_date = Column(String(50), nullable=False)
    due_date = Column(String(50), nullable=True)
    
    supplier_id = Column(String(36), ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    supplier_name_raw = Column(String(255), nullable=True)
    supplier_gstin_raw = Column(String(15), nullable=True)
    supplier_address_raw = Column(Text, nullable=True)

    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    customer_name_raw = Column(String(255), nullable=True)
    customer_gstin_raw = Column(String(15), nullable=True)
    customer_address_raw = Column(Text, nullable=True)

    currency = Column(String(10), default="INR", nullable=False)
    subtotal = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    taxable_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    cgst = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    sgst = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    igst = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_tax = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    discount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    other_charges = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    grand_total = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    payment_terms = Column(String(255), nullable=True)
    purchase_order_number = Column(String(100), nullable=True)
    status = Column(String(50), default="PENDING_APPROVAL", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="invoice")
    organization = relationship("Organization", back_populates="invoices")
    supplier = relationship("Supplier", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    line_number = Column(Integer, default=1, nullable=False)
    description = Column(String(500), nullable=False)
    hsn_sac = Column(String(50), nullable=True)
    quantity = Column(Numeric(15, 3), default=Decimal("1.000"), nullable=False)
    unit = Column(String(20), nullable=True)
    unit_price = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    discount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    invoice = relationship("Invoice", back_populates="line_items")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(50), default="PASSED", nullable=False)  # PASSED, WARNING, FAILED
    is_valid = Column(Boolean, default=True, nullable=False)
    errors = Column(JSON, default=list, nullable=False)
    warnings = Column(JSON, default=list, nullable=False)
    field_explanations = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="validations")


class DuplicateMatch(Base):
    __tablename__ = "duplicate_matches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    match_type = Column(String(50), nullable=False)  # EXACT_HASH, SUPPLIER_INVOICE_NUM, FUZZY_DATE_AMOUNT, SIMILAR_CONTENT
    match_score = Column(Float, default=1.0, nullable=False)
    match_details = Column(JSON, default=dict, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", foreign_keys=[document_id], back_populates="duplicates")


class AnomalyFinding(Base):
    __tablename__ = "anomaly_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True)
    anomaly_type = Column(String(50), nullable=False)  # UNUSUAL_AMOUNT, REPEATED_NUMBER, TAX_MISMATCH, STATISTICAL_DEVIATION, SUSPICIOUS_PATTERN
    severity = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(String(500), nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="anomalies")


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="COMPLETED", nullable=False)
    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    cost_usd = Column(Numeric(10, 6), default=Decimal("0.000000"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="agent_executions")


class WorkflowCheckpoint(Base):
    __tablename__ = "workflow_checkpoints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    thread_id = Column(String(100), nullable=False, index=True)
    checkpoint_state = Column(JSON, nullable=False)
    current_node = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, REPROCESSING_REQUESTED
    assigned_reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(20), default="NORMAL", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    document = relationship("Document", back_populates="approval_request")
    history = relationship("ApprovalHistory", back_populates="approval_request", cascade="all, delete-orphan")


class ApprovalHistory(Base):
    __tablename__ = "approval_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    approval_request_id = Column(String(36), ForeignKey("approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # APPROVE, REJECT, EDIT, REPROCESS
    comments = Column(Text, nullable=True)
    field_changes = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    approval_request = relationship("ApprovalRequest", back_populates="history")
    reviewer = relationship("User")


class ExportRecord(Base):
    __tablename__ = "exports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    export_type = Column(String(50), nullable=False)  # INVOICES, EXPENSES, TAX_SUMMARY, SUPPLIERS
    format = Column(String(20), nullable=False)  # EXCEL, CSV, PDF, JSON
    file_path = Column(String(512), nullable=False)
    record_count = Column(Integer, default=0, nullable=False)
    filters = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=True)
    ip_address = Column(String(50), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(20), default="INFO", nullable=False)  # INFO, SUCCESS, WARNING, ERROR
    is_read = Column(Boolean, default=False, nullable=False)
    link = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class OrganizationSetting(Base):
    __tablename__ = "organization_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    ai_provider = Column(String(50), default="gemini", nullable=False)
    primary_provider = Column(String(50), default="gemini", nullable=False)
    fallback_provider = Column(String(50), default="groq", nullable=False)
    api_key_configured = Column(Boolean, default=False, nullable=False)
    gemini_api_key_masked = Column(String(100), nullable=True)
    groq_api_key_masked = Column(String(100), nullable=True)
    confidence_threshold = Column(Float, default=0.85, nullable=False)
    tax_tolerance = Column(Float, default=2.00, nullable=False)
    auto_approve_threshold = Column(Float, default=0.98, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    monthly_budget_usd = Column(Float, default=100.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="settings")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plan_tier = Column(String(50), default="STARTER", nullable=False)  # STARTER, PROFESSIONAL, ENTERPRISE
    status = Column(String(50), default="TRIAL", nullable=False, index=True)  # TRIAL, ACTIVE, PAST_DUE, CANCELLED, EXPIRED
    monthly_document_limit = Column(Integer, default=50, nullable=False)
    max_users_limit = Column(Integer, default=3, nullable=False)
    current_period_documents_used = Column(Integer, default=0, nullable=False)
    current_period_start = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    billing_cycle = Column(String(20), default="MONTHLY", nullable=False)
    price_amount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    razorpay_customer_id = Column(String(100), nullable=True)
    razorpay_subscription_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="subscription")


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), default="Reviewer", nullable=False)  # Super Admin, Organization Owner, Administrator, Accountant, Reviewer, Read-only User
    invited_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, ACCEPTED, EXPIRED, REVOKED
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="invitations")
    inviter = relationship("User")


