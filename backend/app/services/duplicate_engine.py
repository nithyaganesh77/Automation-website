from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.all_models import Document, Invoice, DuplicateMatch


class DuplicateEngine:
    @classmethod
    def check_duplicates(
        cls, 
        db: Session, 
        document_id: str, 
        organization_id: str, 
        file_hash: str, 
        invoice_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hierarchical duplicate checks:
        1. Exact SHA-256 file hash match.
        2. Exact Supplier + Invoice Number match.
        3. Near-duplicate fuzzy match (same supplier + close date + similar total).
        """
        matches: List[Dict[str, Any]] = []

        # 1. Exact SHA-256 File Hash
        exact_hash_docs = db.query(Document).filter(
            Document.organization_id == organization_id,
            Document.file_hash_sha256 == file_hash,
            Document.id != document_id
        ).all()

        for d in exact_hash_docs:
            matches.append({
                "document_id": document_id,
                "matched_document_id": d.id,
                "match_type": "EXACT_HASH",
                "match_score": 1.0,
                "match_details": {
                    "reason": "Identical SHA-256 cryptographic file checksum",
                    "matched_file_name": d.file_name,
                    "matched_uploaded_at": str(d.created_at)
                }
            })

        # 2. Supplier + Invoice Number Match
        if invoice_data:
            inv_num = invoice_data.get("invoice_number")
            supp_name = invoice_data.get("supplier_name")
            supp_gstin = invoice_data.get("supplier_gstin")
            grand_total = invoice_data.get("grand_total")
            inv_date_str = invoice_data.get("invoice_date")

            if inv_num and inv_num != "INV-UNKNOWN":
                query = db.query(Invoice).join(Document).filter(
                    Invoice.organization_id == organization_id,
                    Invoice.invoice_number == inv_num,
                    Invoice.document_id != document_id
                )
                
                existing_invoices = query.all()
                for existing in existing_invoices:
                    # Check if supplier matches as well
                    same_supplier = False
                    if supp_gstin and existing.supplier_gstin_raw == supp_gstin:
                        same_supplier = True
                    elif supp_name and existing.supplier_name_raw and supp_name.lower().strip() == existing.supplier_name_raw.lower().strip():
                        same_supplier = True

                    if same_supplier:
                        matches.append({
                            "document_id": document_id,
                            "matched_document_id": existing.document_id,
                            "match_type": "SUPPLIER_INVOICE_NUM",
                            "match_score": 0.98,
                            "match_details": {
                                "reason": f"Duplicate invoice number '{inv_num}' for supplier '{existing.supplier_name_raw or supp_name}'",
                                "matched_invoice_id": existing.id,
                                "matched_date": str(existing.invoice_date),
                                "matched_total": float(existing.grand_total)
                            }
                        })
                    else:
                        matches.append({
                            "document_id": document_id,
                            "matched_document_id": existing.document_id,
                            "match_type": "REPEATED_INVOICE_NUM",
                            "match_score": 0.85,
                            "match_details": {
                                "reason": f"Identical invoice number '{inv_num}' found under different supplier records.",
                                "matched_invoice_id": existing.id
                            }
                        })

                # 3. Near-Duplicate Fuzzy Match: Same supplier + Date within 5 days + Grand total within 1%
                if supp_name and grand_total and inv_date_str:
                    try:
                        curr_date = datetime.strptime(inv_date_str, "%Y-%m-%d").date()
                        curr_amt = Decimal(str(grand_total))
                        
                        all_supp_invoices = db.query(Invoice).filter(
                            Invoice.organization_id == organization_id,
                            Invoice.document_id != document_id,
                            Invoice.supplier_name_raw.ilike(f"%{supp_name[:10]}%")
                        ).all()

                        for cand in all_supp_invoices:
                            try:
                                cand_date = datetime.strptime(cand.invoice_date, "%Y-%m-%d").date()
                                days_diff = abs((curr_date - cand_date).days)
                                amt_diff_pct = abs(curr_amt - cand.grand_total) / curr_amt if curr_amt > 0 else 1.0
                                
                                if days_diff <= 5 and amt_diff_pct <= Decimal("0.02") and cand.invoice_number != inv_num:
                                    matches.append({
                                        "document_id": document_id,
                                        "matched_document_id": cand.document_id,
                                        "match_type": "FUZZY_DATE_AMOUNT",
                                        "match_score": 0.78,
                                        "match_details": {
                                            "reason": f"Possible duplicate: Similar date ({cand.invoice_date} vs {inv_date_str}) and amount (₹{cand.grand_total} vs ₹{curr_amt}) from same supplier.",
                                            "days_difference": days_diff,
                                            "amount_difference_percentage": float(amt_diff_pct * 100)
                                        }
                                    })
                            except Exception:
                                continue
                    except Exception:
                        pass

        return matches

