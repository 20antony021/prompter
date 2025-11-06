"""Analytics endpoints."""
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.brand import Brand
from app.models.knowledge_page import KnowledgePage, PageStatus
from app.models.mention import Mention
from app.models.org import Org, OrgMember
from app.models.scan import ScanResult, ScanRun, ScanStatus
from app.models.user import User
from app.schemas.analytics import DashboardStatsResponse, RecentScanResponse, UsageMetric, UsageResponse
from app.services.quotas import get_usage_summary

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    brand_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard statistics for a brand."""
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
            detail="Not authorized to access this brand",
        )

    # Calculate date ranges
    now = datetime.utcnow()
    last_month_start = now - timedelta(days=30)
    prev_month_start = now - timedelta(days=60)
    last_week_start = now - timedelta(days=7)

    # Get scan runs for this brand
    scan_run_ids = [sr.id for sr in brand.scan_runs]

    # Total mentions (current period)
    total_mentions = (
        db.query(func.count(Mention.id))
        .join(ScanResult)
        .filter(
            ScanResult.scan_run_id.in_(scan_run_ids),
            Mention.created_at >= last_month_start,
        )
        .scalar()
        or 0
    )

    # Previous period mentions
    prev_mentions = (
        db.query(func.count(Mention.id))
        .join(ScanResult)
        .filter(
            ScanResult.scan_run_id.in_(scan_run_ids),
            Mention.created_at >= prev_month_start,
            Mention.created_at < last_month_start,
        )
        .scalar()
        or 0
    )

    # Calculate mention growth
    mention_growth = 0.0
    if prev_mentions > 0:
        mention_growth = ((total_mentions - prev_mentions) / prev_mentions) * 100

    # Active pages (published this month)
    active_pages = (
        db.query(func.count(KnowledgePage.id))
        .filter(
            KnowledgePage.brand_id == brand_id,
            KnowledgePage.status == PageStatus.PUBLISHED,
        )
        .scalar()
        or 0
    )

    # Pages published this month
    pages_this_month = (
        db.query(func.count(KnowledgePage.id))
        .filter(
            KnowledgePage.brand_id == brand_id,
            KnowledgePage.status == PageStatus.PUBLISHED,
            KnowledgePage.published_at >= last_month_start,
        )
        .scalar()
        or 0
    )

    # Scan runs (last week)
    scan_runs_count = (
        db.query(func.count(ScanRun.id))
        .filter(
            ScanRun.brand_id == brand_id,
            ScanRun.created_at >= last_week_start,
        )
        .scalar()
        or 0
    )

    # Calculate visibility score
    # Get all mentions with sentiment
    from app.services.mention_extractor import calculate_visibility_score, VISIBILITY_SCORE_VERSION

    brand_mentions = (
        db.query(Mention)
        .join(ScanResult)
        .filter(
            ScanResult.scan_run_id.in_(scan_run_ids),
            Mention.entity_name == brand.name,
            Mention.created_at >= last_month_start,
        )
        .all()
    )

    # Get competitor mention counts
    competitor_mentions = (
        db.query(Mention.entity_name, func.count(Mention.id))
        .join(ScanResult)
        .filter(
            ScanResult.scan_run_id.in_(scan_run_ids),
            Mention.entity_name != brand.name,
            Mention.created_at >= last_month_start,
        )
        .group_by(Mention.entity_name)
        .all()
    )

    competitor_counts = [count for _, count in competitor_mentions]
    brand_positions = [m.position for m in brand_mentions if m.position is not None]
    brand_sentiments = [m.sentiment_score for m in brand_mentions if m.sentiment_score is not None]

    visibility_score = calculate_visibility_score(
        brand_mention_count=len(brand_mentions),
        competitor_mention_counts=competitor_counts,
        brand_positions=brand_positions,
        brand_sentiments=brand_sentiments,
    )

    # Get previous period visibility score for comparison
    prev_brand_mentions = (
        db.query(Mention)
        .join(ScanResult)
        .filter(
            ScanResult.scan_run_id.in_(scan_run_ids),
            Mention.entity_name == brand.name,
            Mention.created_at >= prev_month_start,
            Mention.created_at < last_month_start,
        )
        .all()
    )

    prev_competitor_mentions = (
        db.query(Mention.entity_name, func.count(Mention.id))
        .join(ScanResult)
        .filter(
            ScanResult.scan_run_id.in_(scan_run_ids),
            Mention.entity_name != brand.name,
            Mention.created_at >= prev_month_start,
            Mention.created_at < last_month_start,
        )
        .group_by(Mention.entity_name)
        .all()
    )

    prev_competitor_counts = [count for _, count in prev_competitor_mentions]
    prev_brand_positions = [m.position for m in prev_brand_mentions if m.position is not None]
    prev_brand_sentiments = [
        m.sentiment_score for m in prev_brand_mentions if m.sentiment_score is not None
    ]

    prev_visibility_score = calculate_visibility_score(
        brand_mention_count=len(prev_brand_mentions),
        competitor_mention_counts=prev_competitor_counts,
        brand_positions=prev_brand_positions,
        brand_sentiments=prev_brand_sentiments,
    )

    # Calculate visibility growth
    visibility_growth = 0.0
    if prev_visibility_score > 0:
        visibility_growth = ((visibility_score - prev_visibility_score) / prev_visibility_score) * 100

    # Get recent scans
    recent_scans = (
        db.query(ScanRun)
        .filter(ScanRun.brand_id == brand_id)
        .order_by(ScanRun.created_at.desc())
        .limit(5)
        .all()
    )

    recent_scan_responses = []
    for scan in recent_scans:
        # Get mention count for this scan
        mention_count = (
            db.query(func.count(Mention.id))
            .join(ScanResult)
            .filter(ScanResult.scan_run_id == scan.id)
            .scalar()
            or 0
        )

        # Calculate time ago
        time_diff = now - scan.created_at
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"

        recent_scan_responses.append(
            RecentScanResponse(
                id=scan.id,
                name=f"Scan #{scan.id}",
                models_tested=len(scan.model_matrix_json) if scan.model_matrix_json else 0,
                mentions_found=mention_count,
                time_ago=time_ago,
            )
        )
    
    # Get usage summary for the org
    org = db.query(Org).filter(Org.id == brand.org_id).first()
    usage_data = get_usage_summary(db, org)
    
    usage_response = UsageResponse(
        scans=UsageMetric(**usage_data["scans"]),
        prompts=UsageMetric(**usage_data["prompts"]),
        ai_pages=UsageMetric(**usage_data["ai_pages"]),
    )

    return DashboardStatsResponse(
        visibility_score=round(visibility_score, 1),
        visibility_growth=round(visibility_growth, 1),
        visibility_score_version=VISIBILITY_SCORE_VERSION,
        total_mentions=total_mentions,
        mention_growth=round(mention_growth, 1),
        active_pages=active_pages,
        pages_published_this_month=pages_this_month,
        scan_runs=scan_runs_count,
        recent_scans=recent_scan_responses,
        usage=usage_response,
    )

