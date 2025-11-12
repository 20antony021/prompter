"""Idempotency key tracking for safe retries."""
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class IdempotencyKey(Base):
    """Track idempotency keys to prevent duplicate operations.
    
    When a client retries a request with the same Idempotency-Key header,
    we return the same response without re-executing the operation.
    
    Keys expire after 24 hours to prevent unbounded growth.
    """
    __tablename__ = "idempotency_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    idempotency_key = Column(String(255), nullable=False, unique=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)  # Scope keys to org
    resource_type = Column(String(50), nullable=False)  # e.g. "scan", "page"
    resource_id = Column(Integer, nullable=True)  # ID of created resource
    response_body = Column(Text, nullable=True)  # JSON response to return
    status_code = Column(Integer, nullable=False, default=201)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(hours=24),
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<IdempotencyKey {self.idempotency_key} org={self.org_id} resource={self.resource_type}/{self.resource_id}>"

