from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import decode_token
from app.models.all_models import User, OrganizationMember, Organization

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthenticatedContext:
    def __init__(self, user: User, organization_id: str, role: str):
        self.user = user
        self.organization_id = organization_id
        self.role = role


def get_current_user_context(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> AuthenticatedContext:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception
    
    user_id: Optional[str] = payload.get("sub")
    org_id: Optional[str] = payload.get("org_id")
    role: Optional[str] = payload.get("role", "Viewer")
    
    if not user_id or not org_id:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise credentials_exception

    # Enforce organization membership in DB (Tenant Isolation)
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == org_id
    ).first()
    
    if not member and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this organization"
        )
    
    effective_role = member.role if member else ("Admin" if user.is_superuser else role)
    return AuthenticatedContext(user=user, organization_id=org_id, role=effective_role)


def require_roles(allowed_roles: List[str]):
    def role_checker(auth_ctx: AuthenticatedContext = Depends(get_current_user_context)):
        if auth_ctx.role not in allowed_roles and not auth_ctx.user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires role: {', '.join(allowed_roles)}"
            )
        return auth_ctx
    return role_checker
