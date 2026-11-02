import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Tuple
from app.core.config import settings

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


class ValidationEngine:
    @classmethod
    def validate_invoice(
        cls, 
        invoice_data: Dict[str, Any], 
        tolerance: Decimal = Decimal(str(settings.TAX_TOLERANCE_AMOUNT))
    ) -> Tuple[str, bool, List[Dict[str, str]], List[Dict[str, str]], Dict[str, Any]]:
        """
        Executes strict deterministic financial and structural validation.
        Uses exact Decimal arithmetic.
        Returns: (status, is_valid, errors, warnings, field_explanations)
        """
        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []
        explanations: Dict[str, Any] = {}

        def to_dec(val: Any) -> Decimal:
            if val is None or val == "":
                return Decimal("0.00")
            try:
                return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except Exception:
                return Decimal("0.00")

        # 1. Mandatory Fields
        required_fields = ["invoice_number", "invoice_date", "supplier_name", "grand_total"]
        for field in required_fields:
            val = invoice_data.get(field)
            if val is None or str(val).strip() == "":
                errors.append({
                    "field": field,
                    "code": "MISSING_MANDATORY_FIELD",
                    "message": f"Mandatory field '{field}' is missing from the extracted invoice.",
                    "expected": "Non-empty string/number",
                    "actual": "null"
                })
                explanations[field] = "Failed: Field is mandatory for financial records."
            else:
                explanations[field] = "Passed: Mandatory field present."

        # 2. Date Format and Logical Checks
        inv_date_str = invoice_data.get("invoice_date")
        inv_date = None
        if inv_date_str:
            try:
                inv_date = datetime.strptime(str(inv_date_str), "%Y-%m-%d").date()
                explanations["invoice_date"] = f"Passed: Valid ISO date format ({inv_date_str})."
            except ValueError:
                errors.append({
                    "field": "invoice_date",
                    "code": "INVALID_DATE_FORMAT",
                    "message": f"Invoice date '{inv_date_str}' is not in valid YYYY-MM-DD format.",
                    "expected": "YYYY-MM-DD",
                    "actual": str(inv_date_str)
                })
                explanations["invoice_date"] = "Failed: Invalid ISO date format."

        due_date_str = invoice_data.get("due_date")
        if due_date_str and inv_date:
            try:
                due_date = datetime.strptime(str(due_date_str), "%Y-%m-%d").date()
                if due_date < inv_date:
                    warnings.append({
                        "field": "due_date",
                        "code": "DUE_DATE_PRECEDES_INVOICE",
                        "message": f"Due date ({due_date_str}) occurs prior to invoice date ({inv_date_str})."
                    })
                    explanations["due_date"] = "Warning: Due date is prior to invoice date."
                else:
                    explanations["due_date"] = "Passed: Valid chronological due date."
            except ValueError:
                warnings.append({
                    "field": "due_date",
                    "code": "INVALID_DUE_DATE_FORMAT",
                    "message": f"Due date '{due_date_str}' is not in standard YYYY-MM-DD format."
                })

        # 3. GSTIN Checks
        supplier_gstin = invoice_data.get("supplier_gstin")
        if supplier_gstin:
            if not GSTIN_REGEX.match(str(supplier_gstin).strip()):
                warnings.append({
                    "field": "supplier_gstin",
                    "code": "INVALID_GSTIN_FORMAT",
                    "message": f"Supplier GSTIN '{supplier_gstin}' does not match standard 15-character Indian GSTIN structure."
                })
                explanations["supplier_gstin"] = "Warning: Non-standard GSTIN format pattern."
            else:
                explanations["supplier_gstin"] = "Passed: Standard GSTIN pattern verified."
        else:
            warnings.append({
                "field": "supplier_gstin",
                "code": "MISSING_GSTIN",
                "message": "Supplier GSTIN is not present on invoice. Input Tax Credit (ITC) may not be claimable."
            })
            explanations["supplier_gstin"] = "Warning: Missing supplier GSTIN."

        # 4. Deterministic Financial Math Calculations
        grand_total = to_dec(invoice_data.get("grand_total"))
        subtotal = to_dec(invoice_data.get("subtotal"))
        taxable_amount = to_dec(invoice_data.get("taxable_amount") or subtotal)
        cgst = to_dec(invoice_data.get("cgst"))
        sgst = to_dec(invoice_data.get("sgst"))
        igst = to_dec(invoice_data.get("igst"))
        total_tax = to_dec(invoice_data.get("total_tax"))
        discount = to_dec(invoice_data.get("discount"))
        other_charges = to_dec(invoice_data.get("other_charges"))

        # Negative checks
        if grand_total <= Decimal("0.00"):
            errors.append({
                "field": "grand_total",
                "code": "INVALID_AMOUNT",
                "message": f"Grand total must be strictly positive. Extracted: {grand_total}",
                "expected": "> 0.00",
                "actual": str(grand_total)
            })
        if subtotal < Decimal("0.00") or taxable_amount < Decimal("0.00"):
            errors.append({
                "field": "subtotal",
                "code": "NEGATIVE_AMOUNT",
                "message": "Subtotal or taxable amount cannot be negative.",
                "expected": ">= 0.00",
                "actual": str(subtotal)
            })

        # Tax component consistency: cgst + sgst + igst vs total_tax
        sum_tax_components = (cgst + sgst + igst).quantize(Decimal("0.01"))
        tax_diff = abs(sum_tax_components - total_tax)
        if tax_diff > tolerance:
            warnings.append({
                "field": "total_tax",
                "code": "TAX_COMPONENT_MISMATCH",
                "message": f"Sum of CGST ({cgst}) + SGST ({sgst}) + IGST ({igst}) = {sum_tax_components} does not match total tax ({total_tax}) within ₹{tolerance} tolerance."
            })
            explanations["total_tax"] = f"Warning: Discrepancy of {tax_diff} between tax components and total tax."
        else:
            explanations["total_tax"] = "Passed: Tax components sum matches total tax."

        # Intra-state vs Inter-state GST rules
        if cgst > Decimal("0.00") and igst > Decimal("0.00"):
            warnings.append({
                "field": "igst",
                "code": "MIXED_CGST_IGST",
                "message": "Invoice contains both CGST and IGST simultaneously. In standard Indian GST, transactions are either intra-state (CGST+SGST) or inter-state (IGST)."
            })

        if cgst > Decimal("0.00") and abs(cgst - sgst) > tolerance:
            warnings.append({
                "field": "sgst",
                "code": "CGST_SGST_RATE_MISMATCH",
                "message": f"In intra-state GST, CGST ({cgst}) and SGST ({sgst}) must be identical in rate and amount."
            })

        # Grand Total Consistency: taxable_amount + total_tax + other_charges - discount == grand_total
        expected_grand_total = (taxable_amount + total_tax + other_charges - discount).quantize(Decimal("0.01"))
        grand_diff = abs(expected_grand_total - grand_total)
        if grand_diff > tolerance:
            errors.append({
                "field": "grand_total",
                "code": "GRAND_TOTAL_MATH_MISMATCH",
                "message": f"Mathematical inconsistency: taxable amount ({taxable_amount}) + tax ({total_tax}) + other ({other_charges}) - discount ({discount}) = {expected_grand_total}, but grand total is {grand_total} (Difference: ₹{grand_diff}).",
                "expected": str(expected_grand_total),
                "actual": str(grand_total)
            })
            explanations["grand_total"] = f"Failed: Difference of {grand_diff} exceeds allowable tolerance of {tolerance}."
        else:
            explanations["grand_total"] = f"Passed: Mathematical reconciliation matches within tolerance (Diff: {grand_diff})."

        # 5. Line items consistency
        line_items = invoice_data.get("line_items") or []
        if line_items:
            lines_taxable_sum = Decimal("0.00")
            lines_total_sum = Decimal("0.00")
            for idx, item in enumerate(line_items):
                qty = to_dec(item.get("quantity"))
                price = to_dec(item.get("unit_price"))
                line_disc = to_dec(item.get("discount"))
                line_tax = to_dec(item.get("tax_amount"))
                line_tot = to_dec(item.get("line_total"))

                if qty <= Decimal("0.000"):
                    errors.append({
                        "field": f"line_items[{idx}].quantity",
                        "code": "INVALID_QUANTITY",
                        "message": f"Line #{idx+1} quantity ({qty}) must be greater than zero.",
                        "expected": "> 0",
                        "actual": str(qty)
                    })

                calc_base = (qty * price - line_disc).quantize(Decimal("0.01"))
                lines_taxable_sum += calc_base
                lines_total_sum += line_tot

            # Compare line items sum with taxable amount
            if taxable_amount > Decimal("0.00") and abs(lines_taxable_sum - taxable_amount) > tolerance:
                warnings.append({
                    "field": "line_items",
                    "code": "LINE_ITEMS_SUBTOTAL_MISMATCH",
                    "message": f"Sum of line item base amounts ({lines_taxable_sum}) differs from invoice taxable amount ({taxable_amount}) by {abs(lines_taxable_sum - taxable_amount)}."
                })
                explanations["line_items"] = f"Warning: Line item sum variance of {abs(lines_taxable_sum - taxable_amount)}."
            else:
                explanations["line_items"] = "Passed: Line items correspond to invoice subtotal."

        # Final Status determination
        if errors:
            status = "FAILED"
            is_valid = False
        elif warnings:
            status = "WARNING"
            is_valid = True
        else:
            status = "PASSED"
            is_valid = True

        return status, is_valid, errors, warnings, explanations
