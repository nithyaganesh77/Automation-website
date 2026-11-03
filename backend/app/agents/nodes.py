import time
from decimal import Decimal
from typing import Dict, Any, List
from app.agents.state import DocuMindState
from app.services.storage import StorageService
from app.services.ocr import DocumentParserService
from app.services.llm import LLMService
from app.services.validation_engine import ValidationEngine
from app.services.duplicate_engine import DuplicateEngine
from app.services.anomaly_engine import AnomalyEngine
from app.database.session import SessionLocal
from app.models.all_models import (
    Document, DocumentPage, ExtractedField, Invoice, InvoiceLineItem,
    ValidationResult, DuplicateMatch, AnomalyFinding, AgentExecution,
    ApprovalRequest, Supplier, Notification
)
from app.core.logging import logger


def record_agent_execution(
    db, document_id: str, agent_name: str, status: str, 
    latency_ms: int, tokens_used: int = 0, cost_usd: Decimal = Decimal("0.00"),
    input_payload: Dict[str, Any] = None, output_payload: Dict[str, Any] = None,
    error_message: str = None
):
    try:
        exec_record = AgentExecution(
            document_id=document_id,
            agent_name=agent_name,
            status=status,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            input_payload=input_payload or {},
            output_payload=output_payload or {},
            error_message=error_message
        )
        db.add(exec_record)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record agent execution: {e}")


def intake_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 1: Document Intake Agent"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        # Verify file exists and compute hash
        file_path = state["file_path"]
        file_hash = StorageService.compute_sha256(file_path)
        
        # Check duplicate file hash immediately
        duplicate_matches = DuplicateEngine.check_duplicates(
            db=db,
            document_id=doc_id,
            organization_id=state["organization_id"],
            file_hash=file_hash
        )

        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(
            db, doc_id, "Document Intake Agent", "COMPLETED", latency,
            input_payload={"file_name": state["file_name"], "file_size": state["file_size"]},
            output_payload={"file_hash": file_hash, "exact_duplicate_found": len(duplicate_matches) > 0}
        )

        return {
            "file_hash": file_hash,
            "duplicate_matches": duplicate_matches,
            "current_step": "intake_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "Document Intake Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"Intake error: {str(e)}", "current_step": "intake_failed"}
    finally:
        db.close()


def ocr_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 2: OCR & Text Extraction Agent"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        parsed_pages = DocumentParserService.parse_document(state["file_path"], state["mime_type"])
        
        # Persist pages to DB
        pages_data = []
        full_text_parts = []
        for p in parsed_pages:
            db_page = DocumentPage(
                document_id=doc_id,
                page_number=p.page_number,
                extracted_text=p.text,
                ocr_engine=p.engine,
                confidence=p.confidence,
                page_metadata=p.metadata
            )
            db.add(db_page)
            pages_data.append({
                "page_number": p.page_number,
                "text": p.text,
                "engine": p.engine,
                "confidence": p.confidence
            })
            full_text_parts.append(p.text)

        db.commit()
        full_text = "\n\n".join(full_text_parts)
        latency = int((time.time() - start_time) * 1000)

        record_agent_execution(
            db, doc_id, "OCR Agent", "COMPLETED", latency,
            input_payload={"file_path": state["file_path"], "mime_type": state["mime_type"]},
            output_payload={"page_count": len(pages_data), "total_text_length": len(full_text)}
        )

        return {
            "pages": pages_data,
            "full_text": full_text,
            "current_step": "ocr_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "OCR Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"OCR error: {str(e)}", "current_step": "ocr_failed"}
    finally:
        db.close()


def classification_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 3: Document Classification Agent"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        full_text = state.get("full_text", "")
        doc_type, confidence, details = LLMService.classify_document(full_text)

        # Update Document record in DB
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.document_type = doc_type
            doc.confidence = confidence
            db.commit()

        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(
            db, doc_id, "Classification Agent", "COMPLETED", latency, tokens_used=150,
            cost_usd=Decimal("0.000045"),
            input_payload={"text_snippet": full_text[:300]},
            output_payload={"document_type": doc_type, "confidence": confidence, "details": details}
        )

        return {
            "document_type": doc_type,
            "classification_confidence": confidence,
            "classification_details": details,
            "current_step": "classification_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "Classification Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"Classification error: {str(e)}", "current_step": "classification_failed"}
    finally:
        db.close()


def extraction_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 4: Data Extraction Agent"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        full_text = state.get("full_text", "")
        extracted_data, tokens, cost = LLMService.extract_invoice_data(full_text)

        # Persist extracted fields
        conf_scores = extracted_data.get("confidence_scores", {})
        for field_name, val in extracted_data.items():
            if field_name not in ["line_items", "confidence_scores"]:
                conf = conf_scores.get(field_name, 0.90)
                db_field = ExtractedField(
                    document_id=doc_id,
                    field_name=field_name,
                    field_value=str(val) if val is not None else None,
                    confidence=conf,
                    source_page=1,
                    evidence_text=f"Extracted from document body for {field_name}"
                )
                db.add(db_field)

        # Update document token & cost metrics
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.extracted_tokens = tokens
            doc.estimated_cost_usd = cost

        db.commit()
        latency = int((time.time() - start_time) * 1000)

        record_agent_execution(
            db, doc_id, "Extraction Agent", "COMPLETED", latency, tokens_used=tokens,
            cost_usd=cost,
            input_payload={"document_type": state.get("document_type")},
            output_payload={"extracted_fields_count": len(extracted_data), "invoice_number": extracted_data.get("invoice_number")}
        )

        return {
            "extracted_data": extracted_data,
            "line_items": extracted_data.get("line_items", []),
            "field_confidences": conf_scores,
            "current_step": "extraction_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "Extraction Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"Extraction error: {str(e)}", "current_step": "extraction_failed"}
    finally:
        db.close()


def validation_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 5: Validation Agent (Deterministic financial rules)"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        extracted = state.get("extracted_data", {})
        status, is_valid, errors, warnings, explanations = ValidationEngine.validate_invoice(extracted)

        # Persist validation result
        val_rec = ValidationResult(
            document_id=doc_id,
            status=status,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_explanations=explanations
        )
        db.add(val_rec)
        db.commit()

        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(
            db, doc_id, "Validation Agent", "COMPLETED", latency,
            input_payload={"grand_total": extracted.get("grand_total"), "tax": extracted.get("total_tax")},
            output_payload={"status": status, "is_valid": is_valid, "errors_count": len(errors), "warnings_count": len(warnings)}
        )

        return {
            "validation_status": status,
            "is_valid": is_valid,
            "validation_errors": errors,
            "validation_warnings": warnings,
            "validation_explanations": explanations,
            "current_step": "validation_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "Validation Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"Validation error: {str(e)}", "current_step": "validation_failed"}
    finally:
        db.close()


def duplicate_detection_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 6: Duplicate Detection Agent"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        existing_matches = state.get("duplicate_matches", [])
        new_matches = DuplicateEngine.check_duplicates(
            db=db,
            document_id=doc_id,
            organization_id=state["organization_id"],
            file_hash=state.get("file_hash", ""),
            invoice_data=state.get("extracted_data")
        )

        # Merge and deduplicate matches
        all_matches = {m["matched_document_id"]: m for m in (existing_matches + new_matches)}.values()
        saved_matches = list(all_matches)

        for m in saved_matches:
            dup_rec = DuplicateMatch(
                document_id=doc_id,
                matched_document_id=m["matched_document_id"],
                match_type=m["match_type"],
                match_score=m["match_score"],
                match_details=m["match_details"]
            )
            db.add(dup_rec)
        db.commit()

        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(
            db, doc_id, "Duplicate Detection Agent", "COMPLETED", latency,
            output_payload={"duplicates_detected": len(saved_matches)}
        )

        return {
            "duplicate_matches": saved_matches,
            "current_step": "duplicate_check_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "Duplicate Detection Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"Duplicate detection error: {str(e)}", "current_step": "duplicate_check_failed"}
    finally:
        db.close()


def anomaly_detection_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 7: Anomaly Detection Agent"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        extracted = state.get("extracted_data", {})
        anomalies = AnomalyEngine.detect_anomalies(
            db=db,
            document_id=doc_id,
            organization_id=state["organization_id"],
            invoice_data=extracted
        )

        for anom in anomalies:
            anom_rec = AnomalyFinding(
                document_id=doc_id,
                anomaly_type=anom["anomaly_type"],
                severity=anom["severity"],
                description=anom["description"],
                details=anom["details"]
            )
            db.add(anom_rec)
        db.commit()

        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(
            db, doc_id, "Anomaly Detection Agent", "COMPLETED", latency,
            output_payload={"anomalies_detected": len(anomalies)}
        )

        return {
            "anomaly_findings": anomalies,
            "current_step": "anomaly_check_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "Anomaly Detection Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"Anomaly detection error: {str(e)}", "current_step": "anomaly_check_failed"}
    finally:
        db.close()


def decision_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 8: Decision & Approval Orchestration Agent"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        val_status = state.get("validation_status", "PASSED")
        duplicates = state.get("duplicate_matches", [])
        anomalies = state.get("anomaly_findings", [])
        conf = state.get("classification_confidence", 0.9)

        # High priority or critical anomaly
        has_critical_anomaly = any(a.get("severity") in ["HIGH", "CRITICAL"] for a in anomalies)
        has_duplicate = len(duplicates) > 0

        if val_status == "FAILED":
            decision = "REJECTED_FOR_REVIEW"
            doc_status = "NEEDS_REVIEW"
            approval_status = "PENDING"
            priority = "HIGH"
        elif has_critical_anomaly or has_duplicate or val_status == "WARNING" or conf < 0.85:
            decision = "NEEDS_HUMAN_REVIEW"
            doc_status = "NEEDS_REVIEW"
            approval_status = "PENDING"
            priority = "URGENT" if has_critical_anomaly or has_duplicate else "NORMAL"
        else:
            decision = "APPROVED_FOR_REVIEW"
            doc_status = "NEEDS_REVIEW"
            approval_status = "PENDING"
            priority = "NORMAL"

        # Update Document status
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = doc_status

        # Create or update Approval Request
        existing_req = db.query(ApprovalRequest).filter(ApprovalRequest.document_id == doc_id).first()
        if not existing_req:
            app_req = ApprovalRequest(
                document_id=doc_id,
                organization_id=state["organization_id"],
                status=approval_status,
                priority=priority
            )
            db.add(app_req)

        # In-app notification for human reviewer
        notif = Notification(
            organization_id=state["organization_id"],
            title=f"Approval Required: {state.get('file_name', 'Document')}",
            message=f"Document requires human verification ({decision}). Reason: {val_status} validation, {len(duplicates)} duplicates, {len(anomalies)} anomalies.",
            type="WARNING" if priority in ["HIGH", "URGENT"] else "INFO",
            link=f"/approvals"
        )
        db.add(notif)
        db.commit()

        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(
            db, doc_id, "Decision Agent", "COMPLETED", latency,
            output_payload={"decision": decision, "priority": priority, "doc_status": doc_status}
        )

        return {
            "decision": decision,
            "approval_status": approval_status,
            "current_step": "decision_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "Decision Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"Decision error: {str(e)}", "current_step": "decision_failed"}
    finally:
        db.close()


def finalization_agent_node(state: DocuMindState) -> Dict[str, Any]:
    """Agent 9: Database Finalization & Reporting Preparation Agent"""
    start_time = time.time()
    doc_id = state["document_id"]
    db = SessionLocal()
    try:
        extracted = state.get("extracted_data", {})
        org_id = state["organization_id"]

        # Ensure Supplier exists or create/update supplier
        supp_name = extracted.get("supplier_name") or "Unknown Supplier"
        supp_gstin = extracted.get("supplier_gstin")
        supplier = None
        if supp_name:
            supplier = db.query(Supplier).filter(
                Supplier.organization_id == org_id,
                Supplier.name == supp_name
            ).first()
            if not supplier:
                supplier = Supplier(
                    organization_id=org_id,
                    name=supp_name,
                    gstin=supp_gstin,
                    address=extracted.get("supplier_address")
                )
                db.add(supplier)
                db.flush()

        # Create or update Invoice
        inv = db.query(Invoice).filter(Invoice.document_id == doc_id).first()
        if not inv:
            inv = Invoice(
                document_id=doc_id,
                organization_id=org_id,
                invoice_number=extracted.get("invoice_number", "INV-UNKNOWN"),
                invoice_date=extracted.get("invoice_date", "2026-11-01"),
                due_date=extracted.get("due_date"),
                supplier_id=supplier.id if supplier else None,
                supplier_name_raw=supp_name,
                supplier_gstin_raw=supp_gstin,
                supplier_address_raw=extracted.get("supplier_address"),
                customer_name_raw=extracted.get("customer_name"),
                customer_gstin_raw=extracted.get("customer_gstin"),
                currency=extracted.get("currency", "INR"),
                subtotal=Decimal(str(extracted.get("subtotal") or 0)),
                taxable_amount=Decimal(str(extracted.get("taxable_amount") or extracted.get("subtotal") or 0)),
                cgst=Decimal(str(extracted.get("cgst") or 0)),
                sgst=Decimal(str(extracted.get("sgst") or 0)),
                igst=Decimal(str(extracted.get("igst") or 0)),
                total_tax=Decimal(str(extracted.get("total_tax") or 0)),
                discount=Decimal(str(extracted.get("discount") or 0)),
                other_charges=Decimal(str(extracted.get("other_charges") or 0)),
                grand_total=Decimal(str(extracted.get("grand_total") or 0)),
                payment_terms=extracted.get("payment_terms"),
                purchase_order_number=extracted.get("purchase_order_number"),
                status="PENDING_APPROVAL"
            )
            db.add(inv)
            db.flush()

            # Add line items
            for item in extracted.get("line_items", []):
                li = InvoiceLineItem(
                    invoice_id=inv.id,
                    line_number=item.get("line_number", 1),
                    description=item.get("description", "Item Description"),
                    hsn_sac=item.get("hsn_sac"),
                    quantity=Decimal(str(item.get("quantity") or 1)),
                    unit=item.get("unit", "Nos"),
                    unit_price=Decimal(str(item.get("unit_price") or 0)),
                    discount=Decimal(str(item.get("discount") or 0)),
                    tax_rate=Decimal(str(item.get("tax_rate") or 0)),
                    tax_amount=Decimal(str(item.get("tax_amount") or 0)),
                    line_total=Decimal(str(item.get("line_total") or 0))
                )
                db.add(li)

            # Link invoice_id to validation results
            val = db.query(ValidationResult).filter(ValidationResult.document_id == doc_id).first()
            if val:
                val.invoice_id = inv.id

        db.commit()
        latency = int((time.time() - start_time) * 1000)

        record_agent_execution(
            db, doc_id, "Reporting and Finalization Agent", "COMPLETED", latency,
            output_payload={"invoice_id": inv.id, "grand_total": float(inv.grand_total)}
        )

        return {
            "finalized": True,
            "invoice_id": inv.id,
            "current_step": "workflow_completed"
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        record_agent_execution(db, doc_id, "Reporting and Finalization Agent", "FAILED", latency, error_message=str(e))
        return {"error": f"Finalization error: {str(e)}", "current_step": "finalization_failed"}
    finally:
        db.close()

