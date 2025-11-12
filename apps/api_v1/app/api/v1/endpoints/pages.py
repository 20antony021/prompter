"""Knowledge page endpoints."""
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.deps.quotas import require_page_slot
from app.models.brand import Brand
from app.models.knowledge_page import KnowledgePage, PageStatus
from app.models.org import OrgMember
from app.models.user import User
from app.schemas.page import (
    KnowledgePageCreate,
    KnowledgePageDetailResponse,
    KnowledgePagePublish,
    KnowledgePageResponse,
    KnowledgePageUpdate,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams, decode_cursor, encode_cursor
from app.services.impact_analyzer import ImpactAnalyzer

router = APIRouter()


@router.post("", response_model=KnowledgePageResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_page(
    page_data: KnowledgePageCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new knowledge page (starts generation)."""
    # Verify brand exists and user has access
    brand = db.query(Brand).filter(Brand.id == page_data.brand_id).first()

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
    
    # Check quota and reserve slot
    require_page_slot(brand.org_id, db)

    # Create page in draft status
    from slugify import slugify

    page = KnowledgePage(
        brand_id=page_data.brand_id,
        title=page_data.title,
        slug=slugify(page_data.title),
        status=PageStatus.DRAFT,
    )

    db.add(page)
    db.commit()
    db.refresh(page)

    # Queue generation job using Redis Queue
    try:
        from app.services.job_queue import JobQueueService
        job_service = JobQueueService()
        job_service.enqueue_page_generation(
            page_id=page.id,
            urls_to_crawl=page_data.urls_to_crawl,
            request_id=None,  # Could extract from request headers
            user_id=current_user.id,
            org_id=brand.org_id,
        )
    except Exception as e:
        # Log error but don't fail the request - page is created, just not generated yet
        import logging
        logging.getLogger(__name__).error(f"Failed to enqueue page generation job: {e}", exc_info=True)

    return page


@router.get("/{page_id}", response_model=KnowledgePageDetailResponse)
async def get_knowledge_page(
    page_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get knowledge page by ID."""
    page = db.query(KnowledgePage).filter(KnowledgePage.id == page_id).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    # Verify access
    brand = db.query(Brand).filter(Brand.id == page.brand_id).first()
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

    return page


@router.get("", response_model=PaginatedResponse[KnowledgePageResponse])
async def list_knowledge_pages(
    brand_id: int,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List knowledge pages for a brand with cursor-based pagination.
    
    Returns pages ordered by created_at (newest first).
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    # Build query with pagination
    query = db.query(KnowledgePage).filter(KnowledgePage.brand_id == brand_id).order_by(KnowledgePage.created_at.desc(), KnowledgePage.id.desc())
    
    # Apply cursor if provided
    cursor_data = decode_cursor(pagination.cursor)
    if cursor_data:
        cursor_id = cursor_data.get("id")
        cursor_created_at = cursor_data.get("created_at")
        if cursor_id and cursor_created_at:
            from datetime import datetime
            created_at_dt = datetime.fromisoformat(cursor_created_at)
            query = query.filter(
                (KnowledgePage.created_at < created_at_dt) | 
                ((KnowledgePage.created_at == created_at_dt) & (KnowledgePage.id < cursor_id))
            )

    # Fetch limit + 1 to determine if more results exist
    pages = query.limit(pagination.limit + 1).all()

    # Determine if there are more results
    has_more = len(pages) > pagination.limit
    if has_more:
        pages = pages[: pagination.limit]

    # Generate next cursor
    next_cursor = None
    if has_more and pages:
        last_page = pages[-1]
        next_cursor = encode_cursor(last_page.id, last_page.created_at.isoformat())

    return PaginatedResponse(
        items=pages,
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.put("/{page_id}", response_model=KnowledgePageResponse)
async def update_knowledge_page(
    page_id: int,
    page_data: KnowledgePageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update knowledge page."""
    page = db.query(KnowledgePage).filter(KnowledgePage.id == page_id).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    # Verify access
    brand = db.query(Brand).filter(Brand.id == page.brand_id).first()
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == brand.org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )

    if not org_member or org_member.role.value not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    # Update fields
    if page_data.title is not None:
        page.title = page_data.title
    if page_data.mdx is not None:
        page.mdx = page_data.mdx
    if page_data.canonical_url is not None:
        page.canonical_url = page_data.canonical_url

    db.commit()
    db.refresh(page)

    return page


@router.put("/{page_id}/publish", response_model=KnowledgePageResponse)
async def publish_knowledge_page(
    page_id: int,
    publish_data: KnowledgePagePublish,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish knowledge page to subdomain."""
    page = db.query(KnowledgePage).filter(KnowledgePage.id == page_id).first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    # Verify access
    brand = db.query(Brand).filter(Brand.id == page.brand_id).first()
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == brand.org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )

    if not org_member or org_member.role.value not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    # Update page
    page.status = PageStatus.PUBLISHED
    page.subdomain = publish_data.subdomain
    page.published_at = datetime.utcnow()
    page.path = f"/k/{page.slug}"

    db.commit()
    db.refresh(page)

    return page


@router.get("/{page_id}/impact")
async def get_page_impact(
    page_id: str,
    before_days: int = Query(30, ge=7, le=90, description="Days before publication to analyze"),
    after_days: int = Query(30, ge=7, le=90, description="Days after publication to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze the before/after impact of a published knowledge page.
    
    Compares brand visibility metrics before and after page publication
    to demonstrate ROI and effectiveness.
    
    Metrics analyzed:
    - Mention count changes
    - Sentiment improvements
    - Position improvements (lower is better)
    - Visibility score changes
    
    Statistical significance is assessed to ensure changes are meaningful.
    
    Args:
        page_id: Page ID
        before_days: Days before publication to analyze (default 30)
        after_days: Days after publication to analyze (default 30)
        
    Returns:
        Detailed impact analysis with before/after comparison and insights
    """
    # Verify page exists
    page = await db.get(KnowledgePage, page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Verify user access
    brand = await db.get(Brand, page.brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    # Add proper RBAC check in production
    # Check org membership here
    
    # Get impact analysis
    analyzer = ImpactAnalyzer(db)
    impact = await analyzer.get_page_impact(
        page_id=page_id,
        before_days=before_days,
        after_days=after_days
    )
    
    return impact

