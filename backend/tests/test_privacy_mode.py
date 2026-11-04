import pytest
import socket
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.core.config import settings
from app.services.llm import LLMService, AI_METRICS
from app.models.all_models import Document

SYNTHETIC_INVOICE_TEXT = """
TAX INVOICE
Invoice Number: INV-2026-PRIVACY-01
Invoice Date: 2026-11-03
Supplier: Local Industrial Automation Ltd
GSTIN: 27AABCL9999Z1Z1
Customer: Secure Manufacturing India Pvt Ltd
Customer GSTIN: 27AABCS1111Z1Z2
Subtotal: INR 50,000.00
CGST: INR 4,500.00
SGST: INR 4,500.00
Grand Total: INR 59,000.00
Heavy Machinery Spare Parts | 5 | 10000 | 50000
"""

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SYNTHETIC_PDF_PATH = ROOT_DIR / "evaluation" / "datasets" / "phase2" / "p2_invoice_01_clean_intra.pdf"


def block_all_sockets(*args, **kwargs):
    raise AssertionError("Network socket connection attempted while in PRIVACY MODE!")


def test_privacy_mode_blocks_gemini_and_groq_and_makes_no_network_calls(monkeypatch):
    """
    Step 2 & 3: Prove that when DISABLE_EXTERNAL_AI=True, zero network calls are made,
    Gemini/Groq SDK clients are never called, and local deterministic extraction works.
    """
    # 1. Enforce privacy mode
    monkeypatch.setattr(settings, "DISABLE_EXTERNAL_AI", True)

    # 2. Block all low-level sockets to catch any accidental network traffic
    monkeypatch.setattr(socket.socket, "connect", block_all_sockets)

    # 3. Capture baseline metrics
    initial_gemini_reqs = AI_METRICS["gemini_requests"]
    initial_groq_reqs = AI_METRICS["groq_requests"]
    initial_cost = AI_METRICS["estimated_cost_usd"]

    # 4. Execute classification in privacy mode
    doc_type, confidence, metadata = LLMService.classify_document(SYNTHETIC_INVOICE_TEXT)
    assert doc_type in ["Sales Invoice", "Purchase Invoice"]
    assert confidence > 0.80

    # 5. Execute extraction in privacy mode
    data, tokens, cost = LLMService.extract_invoice_data(SYNTHETIC_INVOICE_TEXT)

    # 6. Verify local deterministic extraction results
    assert data["invoice_number"] == "INV-2026-PRIVACY-01"
    assert data["supplier_gstin"] == "27AABCL9999Z1Z1"
    assert data["customer_gstin"] == "27AABCS1111Z1Z2"
    assert data["subtotal"] == 50000.0
    assert data["cgst"] == 4500.0
    assert data["sgst"] == 4500.0
    assert data["grand_total"] == 59000.0
    assert len(data.get("line_items", [])) >= 1
    assert tokens == 0
    assert cost == 0.0

    # 7. Verify telemetry did not register any external API requests
    assert AI_METRICS["gemini_requests"] == initial_gemini_reqs
    assert AI_METRICS["groq_requests"] == initial_groq_reqs
    assert AI_METRICS["estimated_cost_usd"] == initial_cost

    telemetry = LLMService.get_telemetry()
    assert telemetry["privacy_mode"] is True


def test_privacy_mode_direct_private_methods_raise_runtime_error(monkeypatch):
    """
    Step 4: Prove defense-in-depth — even direct calls to internal provider functions
    are blocked before importing or instantiating Gemini or Groq SDKs.
    """
    monkeypatch.setattr(settings, "DISABLE_EXTERNAL_AI", True)

    with pytest.raises(RuntimeError, match="Privacy mode violation: Gemini classification attempted"):
        LLMService._classify_with_gemini(SYNTHETIC_INVOICE_TEXT)

    with pytest.raises(RuntimeError, match="Privacy mode violation: Groq classification attempted"):
        LLMService._classify_with_groq(SYNTHETIC_INVOICE_TEXT)

    with pytest.raises(RuntimeError, match="Privacy mode violation: Gemini extraction attempted"):
        LLMService._extract_with_gemini(SYNTHETIC_INVOICE_TEXT)

    with pytest.raises(RuntimeError, match="Privacy mode violation: Groq extraction attempted"):
        LLMService._extract_with_groq(SYNTHETIC_INVOICE_TEXT)


def test_test_provider_connection_blocked_in_privacy_mode(monkeypatch):
    """
    Step 4: Prove that test_provider_connection does not send ping requests when in privacy mode.
    """
    monkeypatch.setattr(settings, "DISABLE_EXTERNAL_AI", True)
    # Block sockets
    monkeypatch.setattr(socket.socket, "connect", block_all_sockets)

    ok_gemini, msg_gemini = LLMService.test_provider_connection("gemini", "fake_key_12345")
    assert ok_gemini is False
    assert "Privacy mode is active" in msg_gemini

    ok_groq, msg_groq = LLMService.test_provider_connection("groq", "fake_key_12345")
    assert ok_groq is False
    assert "Privacy mode is active" in msg_groq


from tests.conftest import TestingSessionLocal

def test_full_document_upload_in_privacy_mode(client, test_org_and_admin, db_session, monkeypatch):
    """
    Step 3: End-to-end integration test proving document upload and multi-agent
    workflow complete locally without external AI costs or tokens.
    """
    monkeypatch.setattr(settings, "DISABLE_EXTERNAL_AI", True)
    monkeypatch.setattr(socket.socket, "connect", block_all_sockets)
    monkeypatch.setattr("app.agents.nodes.SessionLocal", TestingSessionLocal)

    token = test_org_and_admin["token"]
    headers = {"Authorization": f"Bearer {token}"}

    with open(SYNTHETIC_PDF_PATH, "rb") as f:
        res = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": ("privacy_test_invoice.pdf", f.read(), "application/pdf")},
            data={"customer_consent": "true"}
        )

    assert res.status_code == 200, f"Upload failed: {res.text}"
    doc_data = res.json()
    doc_id = doc_data["id"]

    # Verify document in DB has zero external AI token/cost footprint
    doc_db = db_session.query(Document).filter(Document.id == doc_id).first()
    assert doc_db is not None
    assert doc_db.extracted_tokens == 0
    assert float(doc_db.estimated_cost_usd) == 0.0
    assert doc_db.status in ["PROCESSED", "NEEDS_REVIEW", "PENDING_APPROVAL"]
