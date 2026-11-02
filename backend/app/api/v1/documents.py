import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.database.session import get_db
from app.models.all_models import Document, Invoice, ValidationResult, AgentExecution
from app.schemas.document import DocumentOut, DocumentDetailOut, DocumentListResponse
from app.api.deps import AuthenticatedContext, get_current_user_context
from app.services.storage import StorageService
from app.agents.graph import execute_document_workflow
from app.agents.state import DocuMindState
from app.services.audit_service import AuditService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentDetailOut)
async def upload_document(
    file: UploadFile = File(...),
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    saved_path, file_hash, file_size, safe_name = await StorageService.save_upload_file(
        file, auth_ctx.organization_id
    )

    # Create Document record
    doc = Document(
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        file_name=file.filename or safe_name,
        file_path=saved_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        file_hash_sha256=file_hash,
        status="PROCESSING",
        document_type="Other"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="DOCUMENT_UPLOADED",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        details={"file_name": doc.file_name, "file_size": file_size, "hash": file_hash}
    )

    # Initialize LangGraph multi-agent workflow state
    state = DocuMindState(
        document_id=doc.id,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        file_path=doc.file_path,
        file_name=doc.file_name,
        file_hash=doc.file_hash_sha256,
        mime_type=doc.mime_type,
        file_size=doc.file_size
    )

    # Execute workflow
    try:
        execute_document_workflow(state)
    except Exception as e:
        doc.status = "FAILED"
        doc.error_message = str(e)
        db.commit()

    db.refresh(doc)
    return doc


@router.post("/bulk-upload", response_model=List[DocumentOut])
async def bulk_upload_documents(
    files: List[UploadFile] = File(...),
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    results = []
    for f in files:
        saved_path, file_hash, file_size, safe_name = await StorageService.save_upload_file(
            f, auth_ctx.organization_id
        )
        doc = Document(
            organization_id=auth_ctx.organization_id,
            user_id=auth_ctx.user.id,
            file_name=f.filename or safe_name,
            file_path=saved_path,
            file_size=file_size,
            mime_type=f.content_type or "application/octet-stream",
            file_hash_sha256=file_hash,
            status="PROCESSING"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        state = DocuMindState(
            document_id=doc.id,
            organization_id=auth_ctx.organization_id,
            user_id=auth_ctx.user.id,
            file_path=doc.file_path,
            file_name=doc.file_name,
            file_hash=doc.file_hash_sha256,
            mime_type=doc.mime_type,
            file_size=doc.file_size
        )
        try:
            execute_document_workflow(state)
        except Exception as e:
            doc.status = "FAILED"
            doc.error_message = str(e)
            db.commit()
            
        db.refresh(doc)
        results.append(doc)

    return results


@router.get("", response_model=DocumentListResponse)
def get_documents(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    # Tenant Isolation: ALWAYS filter by organization_id
    query = db.query(Document).filter(Document.organization_id == auth_ctx.organization_id)

    if status:
        query = query.filter(Document.status == status)
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if search:
        query = query.filter(
            or_(
                Document.file_name.ilike(f"%{search}%"),
                Document.id.ilike(f"%{search}%")
            )
        )
    if supplier:
        query = query.join(Document.invoice).filter(Invoice.supplier_name_raw.ilike(f"%{supplier}%"))

    total = query.count()
    items = query.order_by(desc(Document.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    # Populate summary fields
    out_items = []
    for doc in items:
        inv = doc.invoice
        doc_out = DocumentOut(
            id=doc.id,
            organization_id=doc.organization_id,
            file_name=doc.file_name,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            status=doc.status,
            document_type=doc.document_type,
            confidence=doc.confidence,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            error_message=doc.error_message,
            supplier_name=inv.supplier_name_raw if inv else None,
            invoice_number=inv.invoice_number if inv else None,
            grand_total=float(inv.grand_total) if inv else None
        )
        out_items.append(doc_out)

    total_pages = (total + page_size - 1) // page_size

    return DocumentListResponse(
        items=out_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{document_id}", response_model=DocumentDetailOut)
def get_document_by_id(
    document_id: str,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == auth_ctx.organization_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == auth_ctx.organization_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_name = doc.file_name
    file_path = doc.file_path

    # Clean up physical file
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="DOCUMENT_DELETED",
        entity_type="DOCUMENT",
        entity_id=document_id,
        details={"file_name": file_name}
    )

    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/reprocess", response_model=DocumentDetailOut)
def reprocess_document(
    document_id: str,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == auth_ctx.organization_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "PROCESSING"
    doc.error_message = None
    db.commit()

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="DOCUMENT_REPROCESSING_REQUESTED",
        entity_type="DOCUMENT",
        entity_id=doc.id
    )

    state = DocuMindState(
        document_id=doc.id,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        file_path=doc.file_path,
        file_name=doc.file_name,
        file_hash=doc.file_hash_sha256,
        mime_type=doc.mime_type,
        file_size=doc.file_size
    )
    try:
        execute_document_workflow(state)
    except Exception as e:
        doc.status = "FAILED"
        doc.error_message = str(e)
        db.commit()

    db.refresh(doc)
    return doc


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == auth_ctx.organization_id
    ).first()

    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    return FileResponse(
        path=doc.file_path,
        filename=doc.file_name,
        media_type=doc.mime_type
    )
