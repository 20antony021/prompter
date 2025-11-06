"""Usage and quota endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.org import Org, OrgMember
from app.models.user import User
from app.schemas.analytics import UsageMetric, UsageResponse
from app.services.quotas import get_usage_summary

router = APIRouter()


@router.get("", response_model=UsageResponse)
async def get_usage(
    org_id: int,  # Required to know which org's usage to retrieve
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get usage metrics for an organization's current billing period.
    
    Returns current usage against plan quotas with warning flags.
    Usage resets based on billing_cycle_anchor (purchase date), not calendar month.
    
    **Security:** org_id is validated against authenticated user's memberships.
    Users can only access usage for organizations they belong to.
    """
    # Verify user is member of the org (prevents org-id probing)
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )

    if not org_member:
        # Don't leak whether the org exists - just return forbidden
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization",
        )
    
    # Get org (already validated through membership check above)
    org = db.query(Org).filter(Org.id == org_member.org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    # Get usage summary for current billing period
    usage_data = get_usage_summary(db, org)
    
    return UsageResponse(
        scans=UsageMetric(**usage_data["scans"]),
        prompts=UsageMetric(**usage_data["prompts"]),
        ai_pages=UsageMetric(**usage_data["ai_pages"]),
        period_start=usage_data["period_start"],
        period_end=usage_data["period_end"],
    )

