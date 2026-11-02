from decimal import Decimal
from app.services.validation_engine import ValidationEngine


def test_validation_engine_passing_case():
    invoice_data = {
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-10-15",
        "due_date": "2026-11-15",
        "supplier_name": "Apex Cloud Technologies",
        "supplier_gstin": "29ABCDE1234F1Z5",
        "subtotal": 10000.00,
        "taxable_amount": 10000.00,
        "cgst": 900.00,
        "sgst": 900.00,
        "igst": 0.00,
        "total_tax": 1800.00,
        "discount": 0.00,
        "other_charges": 0.00,
        "grand_total": 11800.00,
        "line_items": [
            {
                "quantity": 1.0,
                "unit_price": 10000.0,
                "discount": 0.0,
                "tax_amount": 1800.0,
                "line_total": 11800.0
            }
        ]
    }
    status, is_valid, errors, warnings, explanations = ValidationEngine.validate_invoice(invoice_data)
    assert is_valid is True
    assert status == "PASSED"
    assert len(errors) == 0


def test_validation_engine_math_mismatch_failure():
    invoice_data = {
        "invoice_number": "INV-MATH-ERR",
        "invoice_date": "2026-10-15",
        "due_date": "2026-11-15",
        "supplier_name": "Apex Cloud Technologies",
        "supplier_gstin": "29ABCDE1234F1Z5",
        "subtotal": 10000.00,
        "taxable_amount": 10000.00,
        "cgst": 900.00,
        "sgst": 900.00,
        "igst": 0.00,
        "total_tax": 1800.00,
        "grand_total": 15000.00  # Discrepancy: 10000 + 1800 != 15000
    }
    status, is_valid, errors, warnings, explanations = ValidationEngine.validate_invoice(invoice_data)
    assert is_valid is False
    assert status == "FAILED"
    assert any(err["code"] == "GRAND_TOTAL_MATH_MISMATCH" for err in errors)


def test_validation_engine_gstin_warning():
    invoice_data = {
        "invoice_number": "INV-2026-002",
        "invoice_date": "2026-10-15",
        "supplier_name": "Apex Cloud",
        "supplier_gstin": "INVALID_GSTIN_123",  # Malformed GSTIN
        "grand_total": 1000.00,
        "subtotal": 1000.00,
        "total_tax": 0.00
    }
    status, is_valid, errors, warnings, explanations = ValidationEngine.validate_invoice(invoice_data)
    assert any(w["code"] == "INVALID_GSTIN_FORMAT" for w in warnings)

