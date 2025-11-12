"""Audit log model for tracking user actions."""
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON

from app.database import Base


class AuditAction(str, enum.Enum):
    """Audit action types."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"


class AuditLog(Base):
    """
    Audit log model for compliance and security tracking.
    
    Captures who did what, when, and where for all sensitive operations.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Action details
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)  # e.g., 'brand', 'scan_run'
    resource_id = Column(Integer, nullable=True, index=True)  # ID of affected resource
    
    # Context
    details = Column(JSON, nullable=True)  # Additional context (changes, filters, etc.)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)  # For request correlation
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Legacy field, kept for compatibility
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action.value}, resource={self.resource_type}#{self.resource_id})>"

