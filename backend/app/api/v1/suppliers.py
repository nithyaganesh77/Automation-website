from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.session import get_db
from app.models.all_models import Supplier
from app.schemas.supplier import SupplierOut, SupplierCreateRequest, SupplierUpdateRequest
from app.api.deps import AuthenticatedContext, get_current_user_context
from app.services.audit_service import AuditService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=List[SupplierOut])
def get_suppliers(
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None)
):
    query = db.query(Supplier).filter(Supplier.organization_id == auth_ctx.organization_id)
    if search:
        query = query.filter(Supplier.name.ilike(f"%{search}%"))
    return query.order_by(desc(Supplier.total_spend)).all()


@router.post("", response_model=SupplierOut)
def create_supplier(
    req: SupplierCreateRequest,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    existing = db.query(Supplier).filter(
        Supplier.organization_id == auth_ctx.organization_id,
        Supplier.name == req.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Supplier with this name already exists")

    supplier = Supplier(
        organization_id=auth_ctx.organization_id,
        name=req.name,
        gstin=req.gstin,
        pan=req.pan,
        address=req.address,
        city=req.city,
        state=req.state,
        postal_code=req.postal_code,
        country=req.country,
        email=req.email,
        phone=req.phone
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    AuditService.log_event(
        db=db,
        organization_id=auth_ctx.organization_id,
        user_id=auth_ctx.user.id,
        action="SUPPLIER_CREATED",
        entity_type="SUPPLIER",
        entity_id=supplier.id,
        details={"name": supplier.name}
    )

    return supplier


@router.patch("/{supplier_id}", response_model=SupplierOut)
def update_supplier(
    supplier_id: str,
    req: SupplierUpdateRequest,
    auth_ctx: AuthenticatedContext = Depends(get_current_user_context),
    db: Session = Depends(get_db)
):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.organization_id == auth_ctx.organization_id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for field, val in req.model_dump(exclude_unset=True).items():
        if val is not None:
            setattr(supplier, field, val)

    db.commit()
    db.refresh(supplier)
    return supplier

