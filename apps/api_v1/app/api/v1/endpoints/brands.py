"""Brand endpoints with pagination, auth, and audit logging."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.deps.quotas import require_brand_slot
from app.models.audit_log import AuditAction
from app.models.brand import Brand, Competitor
from app.models.org import OrgMember
from app.models.user import User
from app.schemas.brand import (
    BrandCreate,
    BrandResponse,
    BrandUpdate,
    CompetitorCreate,
    CompetitorResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams, decode_cursor, encode_cursor
from app.services.audit_logger import AuditLogger, get_audit_context
from app.services.competitor_analyzer import CompetitorAnalyzer

router = APIRouter()


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_data: BrandCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    org_member: OrgMember = Depends(require_admin()),
    db: Session = Depends(get_db),
):
    """Create a new brand (requires admin role)."""
    # Verify user is admin of the org
    if org_member.org_id != brand_data.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this organization",
        )
    
    # Check quota
    require_brand_slot(brand_data.org_id, db)

    brand = Brand(
        org_id=brand_data.org_id,
        name=brand_data.name,
        website=str(brand_data.website),
        primary_domain=brand_data.primary_domain,
    )

    db.add(brand)
    db.commit()
    db.refresh(brand)

    # Audit log
    audit_ctx = get_audit_context(request, current_user, org_member.org_id)
    AuditLogger.log_create(
        db=db,
        resource_type="brand",
        resource_id=brand.id,
        details={"name": brand.name, "website": brand.website},
        **audit_ctx,
    )

    return brand


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get brand by ID."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    # Verify user has access to this brand's org
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
            detail="Not authorized to view this brand",
        )

    return brand


@router.get("", response_model=PaginatedResponse[BrandResponse])
async def list_brands(
    org_id: int,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List brands for an organization with cursor-based pagination.
    
    Requires user to be member of the organization.
    """
    # Verify user is member of the org
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )

    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization",
        )

    # Build query with org scoping
    query = db.query(Brand).filter(Brand.org_id == org_id).order_by(Brand.created_at.desc(), Brand.id.desc())

    # Apply cursor if provided
    cursor_data = decode_cursor(pagination.cursor)
    if cursor_data:
        cursor_id = cursor_data.get("id")
        cursor_created_at = cursor_data.get("created_at")
        if cursor_id and cursor_created_at:
            from datetime import datetime
            created_at_dt = datetime.fromisoformat(cursor_created_at)
            query = query.filter(
                (Brand.created_at < created_at_dt) | 
                ((Brand.created_at == created_at_dt) & (Brand.id < cursor_id))
            )

    # Fetch limit + 1 to determine if more results exist
    brands = query.limit(pagination.limit + 1).all()

    # Determine if there are more results
    has_more = len(brands) > pagination.limit
    if has_more:
        brands = brands[: pagination.limit]

    # Generate next cursor
    next_cursor = None
    if has_more and brands:
        last_brand = brands[-1]
        next_cursor = encode_cursor(last_brand.id, last_brand.created_at.isoformat())

    return PaginatedResponse(items=brands, next_cursor=next_cursor, has_more=has_more)


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    brand_data: BrandUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update brand (requires admin role)."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    # Verify user is admin of the org
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
            detail="Not authorized to update this brand",
        )

    # Track changes for audit log
    changes = {}
    if brand_data.name is not None and brand_data.name != brand.name:
        changes["name"] = {"old": brand.name, "new": brand_data.name}
        brand.name = brand_data.name
    if brand_data.website is not None and str(brand_data.website) != brand.website:
        changes["website"] = {"old": brand.website, "new": str(brand_data.website)}
        brand.website = str(brand_data.website)
    if brand_data.primary_domain is not None and brand_data.primary_domain != brand.primary_domain:
        changes["primary_domain"] = {"old": brand.primary_domain, "new": brand_data.primary_domain}
        brand.primary_domain = brand_data.primary_domain

    db.commit()
    db.refresh(brand)

    # Audit log
    if changes:
        audit_ctx = get_audit_context(request, current_user, org_member.org_id)
        AuditLogger.log_update(
            db=db,
            resource_type="brand",
            resource_id=brand.id,
            changes=changes,
            **audit_ctx,
        )

    return brand


@router.post(
    "/{brand_id}/competitors",
    response_model=CompetitorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_competitor(
    brand_id: int,
    competitor_data: CompetitorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add competitor to brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    # Verify user has access
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

    competitor = Competitor(
        brand_id=brand_id,
        name=competitor_data.name,
        website=str(competitor_data.website),
    )

    db.add(competitor)
    db.commit()
    db.refresh(competitor)

    return competitor


@router.get("/{brand_id}/competitors", response_model=List[CompetitorResponse])
async def list_competitors(
    brand_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List competitors for a brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    competitors = db.query(Competitor).filter(Competitor.brand_id == brand_id).all()
    return competitors


@router.get("/{brand_id}/competitor-analysis")
async def get_competitor_analysis(
    brand_id: str,
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze (7, 30, or 90)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive competitor analysis.
    
    Analyzes competitive landscape including:
    - Brand vs competitor metrics (mentions, sentiment, position)
    - Market share calculation
    - Rankings by different metrics
    - Competitive positioning
    
    Args:
        brand_id: Brand ID
        days: Number of days to analyze (default 30)
        
    Returns:
        Detailed competitor analysis with rankings and market share
    """
    # Verify brand exists and user has access
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    # Verify user access (simplified - add proper RBAC in production)
    # Check org membership here
    
    # Get competitor analysis
    analyzer = CompetitorAnalyzer(db)
    analysis = await analyzer.get_competitor_analysis(
        brand_id=brand_id,
        days=days
    )
    
    return analysis


@router.get("/{brand_id}/competitive-positioning")
async def get_competitive_positioning(
    brand_id: str,
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get competitive positioning analysis.
    
    Classifies brands into quadrants based on mentions vs sentiment:
    - Leaders: High mentions, high sentiment
    - Challengers: High mentions, low sentiment
    - Niche Positive: Low mentions, high sentiment
    - Emerging: Low mentions, low sentiment
    
    Args:
        brand_id: Brand ID
        days: Number of days to analyze
        
    Returns:
        Quadrant classification with actionable insights
    """
    # Verify brand exists
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    # Get positioning analysis
    analyzer = CompetitorAnalyzer(db)
    positioning = await analyzer.get_competitive_positioning(
        brand_id=brand_id,
        days=days
    )
    
    return positioning

