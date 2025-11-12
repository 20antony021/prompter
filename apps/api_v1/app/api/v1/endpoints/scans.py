"""Scan endpoints."""
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.deps.quotas import require_scan_credit
from app.models.brand import Brand
from app.models.mention import Mention
from app.models.org import OrgMember
from app.models.scan import ScanRun, ScanStatus
from app.models.user import User
from app.schemas.scan import (
    MentionResponse,
    ScanRunCreate,
    ScanRunDetailResponse,
    ScanRunResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams, decode_cursor, encode_cursor
from app.services.idempotency import check_idempotency_key, store_idempotency_key

router = APIRouter()


@router.post("", response_model=ScanRunResponse, status_code=status.HTTP_201_CREATED)
async def create_scan_run(
    scan_data: ScanRunCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create and queue a new scan run.
    
    Supports idempotent retries via Idempotency-Key header.
    If a request with the same key is retried, returns the original response
    without creating a duplicate scan or consuming additional credits.
    """
    # Verify brand exists and user has access
    brand = db.query(Brand).filter(Brand.id == scan_data.brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    # Verify user is member of brand's org
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == brand.org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    
    # Check for idempotency key (prevents double-spend on retries)
    cached_response = check_idempotency_key(request, db, brand.org_id, "scan")
    if cached_response:
        status_code, response_body = cached_response
        return response_body
    
    # Check scan credits for all models in the matrix
    # Calculate total credits needed upfront
    total_credits_needed = 0
    for model_name in scan_data.models:
        # Perplexity online models count as 2 scans
        credits = 2 if "perplexity" in model_name.lower() and "online" in model_name.lower() else 1
        total_credits_needed += credits
    
    # Reserve all credits at once
    if scan_data.models:
        from app.services.quotas import get_or_create_usage, get_plan, assert_within_limit
        from app.models.org import Org
        
        org = db.query(Org).filter(Org.id == brand.org_id).first()
        plan = get_plan(org)
        usage = get_or_create_usage(db, org)
        
        # Check if we have enough credits for all scans
        assert_within_limit(usage.scans_used + total_credits_needed, plan["scans"], "Scan")
        
        # Reserve the credits
        usage.scans_used += total_credits_needed
        db.commit()

    # Create scan run
    scan_run = ScanRun(
        brand_id=scan_data.brand_id,
        prompt_set_id=scan_data.prompt_set_id,
        status=ScanStatus.QUEUED,
        model_matrix_json=scan_data.models,
    )

    db.add(scan_run)
    db.commit()
    db.refresh(scan_run)

    # Queue background job using Redis Queue
    try:
        from app.services.job_queue import JobQueueService
        job_service = JobQueueService()
        job_service.enqueue_scan(
            scan_run_id=scan_run.id,
            idempotency_key=idempotency_key,
            request_id=request.headers.get("X-Request-ID"),
            user_id=current_user.id,
            org_id=brand.org_id,
        )
    except Exception as e:
        # Log error but don't fail the request - scan is created, just not queued yet
        import logging
        logging.getLogger(__name__).error(f"Failed to enqueue scan job: {e}", exc_info=True)

    # Store idempotency key if provided
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        from app.schemas.scan import ScanRunResponse as ResponseSchema
        response_dict = ResponseSchema.from_orm(scan_run).dict()
        store_idempotency_key(
            idempotency_key=idempotency_key,
            db=db,
            org_id=brand.org_id,
            resource_type="scan",
            resource_id=scan_run.id,
            response_body=response_dict,
            status_code=201
        )

    return scan_run


@router.get("/{scan_id}", response_model=ScanRunDetailResponse)
async def get_scan_run(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get scan run by ID with results."""
    scan_run = db.query(ScanRun).filter(ScanRun.id == scan_id).first()

    if not scan_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan run not found",
        )

    # Verify access
    brand = db.query(Brand).filter(Brand.id == scan_run.brand_id).first()
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == brand.org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    return scan_run


@router.get("", response_model=PaginatedResponse[ScanRunResponse])
async def list_scan_runs(
    brand_id: int,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List scan runs for a brand with cursor-based pagination.
    
    Returns scan runs ordered by created_at (newest first).
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    # Verify access
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == brand.org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    # Build query with pagination
    query = db.query(ScanRun).filter(ScanRun.brand_id == brand_id).order_by(ScanRun.created_at.desc(), ScanRun.id.desc())
    
    # Apply cursor if provided
    cursor_data = decode_cursor(pagination.cursor)
    if cursor_data:
        cursor_id = cursor_data.get("id")
        cursor_created_at = cursor_data.get("created_at")
        if cursor_id and cursor_created_at:
            from datetime import datetime
            created_at_dt = datetime.fromisoformat(cursor_created_at)
            query = query.filter(
                (ScanRun.created_at < created_at_dt) | 
                ((ScanRun.created_at == created_at_dt) & (ScanRun.id < cursor_id))
            )

    # Fetch limit + 1 to determine if more results exist
    scan_runs = query.limit(pagination.limit + 1).all()

    # Determine if there are more results
    has_more = len(scan_runs) > pagination.limit
    if has_more:
        scan_runs = scan_runs[: pagination.limit]

    # Generate next cursor
    next_cursor = None
    if has_more and scan_runs:
        last_scan = scan_runs[-1]
        next_cursor = encode_cursor(last_scan.id, last_scan.created_at.isoformat())

    return PaginatedResponse(
        items=scan_runs,
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/mentions", response_model=List[MentionResponse])
async def list_mentions(
    brand_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List mentions for a brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    # Get all scan runs for this brand
    scan_run_ids = [sr.id for sr in brand.scan_runs]

    # Get mentions
    from app.models.scan import ScanResult

    mentions = (
        db.query(Mention)
        .join(ScanResult)
        .filter(ScanResult.scan_run_id.in_(scan_run_ids))
        .order_by(Mention.created_at.desc())
        .limit(limit)
        .all()
    )

    return mentions

