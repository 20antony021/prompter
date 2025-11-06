"""Idempotency service for safe client retries."""
import json
from datetime import datetime
from typing import Optional, Tuple

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyKey


def check_idempotency_key(
    request: Request,
    db: Session,
    org_id: int,
    resource_type: str
) -> Optional[Tuple[int, dict]]:
    """Check if this request has been processed before.
    
    Args:
        request: FastAPI request object
        db: Database session
        org_id: Organization ID (scope keys to org)
        resource_type: Type of resource being created (e.g. "scan", "page")
    
    Returns:
        None if this is a new request
        Tuple of (status_code, response_body) if this is a duplicate
    
    Raises:
        HTTPException 400 if idempotency key is invalid
    """
    idempotency_key = request.headers.get("Idempotency-Key")
    
    if not idempotency_key:
        return None
    
    # Validate key format (should be UUID or similar)
    if len(idempotency_key) < 16 or len(idempotency_key) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Idempotency-Key format (must be 16-255 chars)"
        )
    
    # Check if we've seen this key before
    existing = (
        db.query(IdempotencyKey)
        .filter(
            IdempotencyKey.idempotency_key == idempotency_key,
            IdempotencyKey.org_id == org_id,
            IdempotencyKey.resource_type == resource_type,
            IdempotencyKey.expires_at > datetime.utcnow()
        )
        .first()
    )
    
    if existing:
        # Return cached response
        response_body = json.loads(existing.response_body) if existing.response_body else {}
        return (existing.status_code, response_body)
    
    return None


def store_idempotency_key(
    idempotency_key: str,
    db: Session,
    org_id: int,
    resource_type: str,
    resource_id: int,
    response_body: dict,
    status_code: int = 201
) -> None:
    """Store an idempotency key with its response.
    
    Args:
        idempotency_key: The idempotency key from the request
        db: Database session
        org_id: Organization ID
        resource_type: Type of resource created
        resource_id: ID of the created resource
        response_body: JSON response to cache
        status_code: HTTP status code
    """
    if not idempotency_key:
        return
    
    # Check if already exists (race condition protection)
    existing = (
        db.query(IdempotencyKey)
        .filter(
            IdempotencyKey.idempotency_key == idempotency_key,
            IdempotencyKey.org_id == org_id,
            IdempotencyKey.resource_type == resource_type
        )
        .first()
    )
    
    if existing:
        # Already stored (concurrent request beat us)
        return
    
    # Store new key
    key_record = IdempotencyKey(
        idempotency_key=idempotency_key,
        org_id=org_id,
        resource_type=resource_type,
        resource_id=resource_id,
        response_body=json.dumps(response_body),
        status_code=status_code
    )
    db.add(key_record)
    db.commit()


def cleanup_expired_keys(db: Session, batch_size: int = 1000) -> int:
    """Delete expired idempotency keys (run as background job).
    
    Args:
        db: Database session
        batch_size: Max number of keys to delete per run
    
    Returns:
        Number of keys deleted
    """
    deleted = (
        db.query(IdempotencyKey)
        .filter(IdempotencyKey.expires_at <= datetime.utcnow())
        .limit(batch_size)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted

