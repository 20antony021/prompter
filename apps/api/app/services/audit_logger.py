"""Audit logging service."""
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditAction

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Service for logging audit events.
    
    Captures:
    - Who: user_id
    - What: action, resource_type, resource_id
    - When: timestamp
    - Where: IP address, user agent
    - How: request_id, changes made
    """

    @staticmethod
    def log(
        db: Session,
        user_id: int,
        org_id: int,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            db: Database session
            user_id: ID of user performing action
            org_id: ID of organization (for multi-tenancy)
            action: Type of action (CREATE, UPDATE, DELETE, etc.)
            resource_type: Type of resource affected (e.g., 'brand', 'scan_run')
            resource_id: ID of affected resource
            details: Additional context (e.g., changed fields, old/new values)
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request ID for correlation
        
        Returns:
            Created audit log entry
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                org_id=org_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                created_at=datetime.utcnow(),
            )

            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)

            logger.info(
                f"Audit: {action.value} {resource_type}#{resource_id} by user#{user_id} org#{org_id}",
                extra={
                    "user_id": user_id,
                    "org_id": org_id,
                    "action": action.value,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "request_id": request_id,
                },
            )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}", exc_info=True)
            # Don't fail the main operation if audit logging fails
            return None

    @staticmethod
    def log_create(
        db: Session,
        user_id: int,
        org_id: int,
        resource_type: str,
        resource_id: int,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditLog:
        """Log a CREATE action."""
        return AuditLogger.log(
            db=db,
            user_id=user_id,
            org_id=org_id,
            action=AuditAction.CREATE,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            **kwargs,
        )

    @staticmethod
    def log_update(
        db: Session,
        user_id: int,
        org_id: int,
        resource_type: str,
        resource_id: int,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditLog:
        """Log an UPDATE action with changed fields."""
        details = {"changes": changes} if changes else None
        return AuditLogger.log(
            db=db,
            user_id=user_id,
            org_id=org_id,
            action=AuditAction.UPDATE,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            **kwargs,
        )

    @staticmethod
    def log_delete(
        db: Session,
        user_id: int,
        org_id: int,
        resource_type: str,
        resource_id: int,
        **kwargs,
    ) -> AuditLog:
        """Log a DELETE action."""
        return AuditLogger.log(
            db=db,
            user_id=user_id,
            org_id=org_id,
            action=AuditAction.DELETE,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )

    @staticmethod
    def log_access(
        db: Session,
        user_id: int,
        org_id: int,
        resource_type: str,
        resource_id: int,
        **kwargs,
    ) -> AuditLog:
        """Log a READ/ACCESS action (for sensitive resources)."""
        return AuditLogger.log(
            db=db,
            user_id=user_id,
            org_id=org_id,
            action=AuditAction.READ,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs,
        )


def get_audit_context(request, user, org_id: int) -> Dict[str, Any]:
    """
    Extract audit context from request.
    
    Args:
        request: FastAPI Request object
        user: Authenticated user
        org_id: Organization ID
    
    Returns:
        Dictionary with audit context (ip_address, user_agent, request_id)
    """
    return {
        "user_id": user.id,
        "org_id": org_id,
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent"),
        "request_id": getattr(request.state, "request_id", None),
    }

