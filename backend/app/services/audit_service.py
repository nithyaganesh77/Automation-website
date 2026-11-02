from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.all_models import AuditLog, Notification


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        organization_id: str,
        action: str,
        entity_type: str,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Records an immutable audit trail entry."""
        log_entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            details=details or {}
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def create_notification(
        db: Session,
        organization_id: str,
        title: str,
        message: str,
        notification_type: str = "INFO",
        user_id: Optional[str] = None,
        link: Optional[str] = None
    ) -> Notification:
        notif = Notification(
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            link=link
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif
