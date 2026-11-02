from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.all_models import User, Organization, OrganizationMember, OrganizationSetting
from app.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, TokenResponse,
    RefreshTokenRequest, ForgotPasswordRequest, UserOut
)
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.api.deps import AuthenticatedContext, get_current_user_context
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == req.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Create Organization
    org_slug = req.organization_name.lower().replace(" ", "-")[:50]
    # Ensure unique slug
    base_slug = org_slug
    idx = 1
    while db.query(Organization).filter(Organization.slug == org_slug).first():
        org_slug = f"{base_slug}-{idx}"
        idx += 1

    org = Organization(name=req.organization_name, slug=org_slug)
    db.add(org)
    db.flush()

    # Create default Organization Settings
    org_setting = OrganizationSetting(
        organization_id=org.id,
        ai_provider="gemini",
        currency="INR"
    )
    db.add(org_setting)

    # Create User
    hashed_pwd = hash_password(req.password)
    user = User(
        email=req.email.lower(),
        hashed_password=hashed_pwd,
        full_name=req.full_name,
        is_active=True
    )
    db.add(user)
    db.flush()

    # Add User as Admin of the new Organization
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="Admin"
    )
    db.add(member)
    db.commit()

    # Audit log
    AuditService.log_event(
        db=db,
        organization_id=org.id,
        user_id=user.id,
        action="USER_REGISTERED",
        entity_type="USER",
        entity_id=user.id,
        details={"email": user.email, "organization": org.name}
    )

    access_token = create_access_token(user.id, org.id, "Admin")
    refresh_token = create_refresh_token(user.id, org.id)

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        organization={"id": org.id, "name": org.name, "slug": org.slug},
        role="Admin"
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_out
    )


@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Get primary organization membership
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to any organization."
        )

    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()

    access_token = create_access_token(user.id, org.id, membership.role)
    refresh_token = create_refresh_token(user.id, org.id)

    AuditService.log_event(
        db=db,
        organization_id=org.id,
        user_id=user.id,
        action="USER_LOGGED_IN",
        entity_type="USER",
        entity_id=user.id
    )

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        organization={"id": org.id, "name": org.name, "slug": org.slug},
        role=membership.role
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_out
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == org_id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Membership revoked.")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    access_token = create_access_token(user.id, org_id, member.role)
    new_refresh = create_refresh_token(user.id, org_id)

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        organization={"id": org.id, "name": org.name, "slug": org.slug},
        role=member.role
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        user=user_out
    )


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Standard security practice: return success message whether email exists or not
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if user:
        AuditService.log_event(
            db=db,
            organization_id="system",
            action="PASSWORD_RESET_REQUESTED",
            entity_type="USER",
            entity_id=user.id,
            details={"email": user.email}
        )
    return {"message": "If this email is registered, password reset instructions have been generated."}


@router.get("/me", response_model=UserOut)
def get_current_user(auth_ctx: AuthenticatedContext = Depends(get_current_user_context), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == auth_ctx.organization_id).first()
    return UserOut(
        id=auth_ctx.user.id,
        email=auth_ctx.user.email,
        full_name=auth_ctx.user.full_name,
        is_active=auth_ctx.user.is_active,
        is_superuser=auth_ctx.user.is_superuser,
        organization={"id": org.id, "name": org.name, "slug": org.slug} if org else None,
        role=auth_ctx.role
    )
