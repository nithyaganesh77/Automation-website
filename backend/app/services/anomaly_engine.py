from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.all_models import Invoice, Supplier


class AnomalyEngine:
    @classmethod
    def detect_anomalies(
        cls, 
        db: Session, 
        document_id: str, 
        organization_id: str, 
        invoice_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []

        grand_total = Decimal(str(invoice_data.get("grand_total") or 0))
        taxable_amount = Decimal(str(invoice_data.get("taxable_amount") or invoice_data.get("subtotal") or 0))
        total_tax = Decimal(str(invoice_data.get("total_tax") or 0))
        supp_name = invoice_data.get("supplier_name")

        # 1. Tax Rate Slab Anomaly
        if taxable_amount > Decimal("0.00") and total_tax > Decimal("0.00"):
            effective_rate = round((total_tax / taxable_amount) * 100, 1)
            standard_slabs = [0.0, 5.0, 12.0, 18.0, 28.0]
            closest_slab = min(standard_slabs, key=lambda s: abs(float(effective_rate) - s))
            
            if abs(float(effective_rate) - closest_slab) > 1.5:
                findings.append({
                    "document_id": document_id,
                    "anomaly_type": "UNEXPECTED_TAX_RATE",
                    "severity": "MEDIUM",
                    "description": f"Calculated effective tax rate is {effective_rate}%, which deviates from standard GST tax slabs (0%, 5%, 12%, 18%, 28%).",
                    "details": {
                        "effective_tax_rate_percent": float(effective_rate),
                        "closest_standard_slab": closest_slab,
                        "taxable_amount": float(taxable_amount),
                        "total_tax": float(total_tax)
                    }
                })

        # 2. Historical Supplier Spend Deviation (Statistical Anomaly)
        if supp_name:
            avg_query = db.query(
                func.avg(Invoice.grand_total).label("avg_spend"),
                func.count(Invoice.id).label("count")
            ).filter(
                Invoice.organization_id == organization_id,
                Invoice.supplier_name_raw.ilike(f"%{supp_name[:12]}%")
            ).first()

            if avg_query and avg_query.count and avg_query.count >= 3:
                historical_avg = Decimal(str(avg_query.avg_spend))
                if grand_total > (historical_avg * Decimal("3.0")):
                    findings.append({
                        "document_id": document_id,
                        "anomaly_type": "STATISTICAL_DEVIATION",
                        "severity": "HIGH",
                        "description": f"Invoice amount (₹{grand_total:,.2f}) is over 3x higher than historical average spend (₹{historical_avg:,.2f}) for supplier '{supp_name}'.",
                        "details": {
                            "historical_average": float(historical_avg),
                            "historical_invoice_count": avg_query.count,
                            "current_amount": float(grand_total),
                            "multiplier": float(round(grand_total / historical_avg, 2))
                        }
                    })

        # 3. Round Number Anomaly on High Amounts (> ₹50,000 without tax breakdown or exact cents)
        if grand_total >= Decimal("50000.00"):
            if grand_total % Decimal("1000.00") == Decimal("0.00") and total_tax == Decimal("0.00"):
                findings.append({
                    "document_id": document_id,
                    "anomaly_type": "SUSPICIOUS_ROUND_NUMBER",
                    "severity": "LOW",
                    "description": f"Large rounded total (₹{grand_total:,.2f}) without explicit tax calculation may indicate an informal bill or estimate.",
                    "details": {"amount": float(grand_total)}
                })

        # 4. Weekend Invoice Date Anomaly
        inv_date_str = invoice_data.get("invoice_date")
        if inv_date_str:
            try:
                from datetime import datetime
                inv_dt = datetime.strptime(str(inv_date_str), "%Y-%m-%d")
                if inv_dt.weekday() == 6:  # Sunday
                    findings.append({
                        "document_id": document_id,
                        "anomaly_type": "WEEKEND_INVOICE_DATE",
                        "severity": "LOW",
                        "description": f"Invoice date ({inv_date_str}) is a Sunday. Please verify legitimate vendor billing schedule.",
                        "details": {"weekday": "Sunday"}
                    })
            except Exception:
                pass

        return findings
