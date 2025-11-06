"""Quota management and enforcement service."""
from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from dateutil.relativedelta import relativedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import PLAN_QUOTAS, WARN_THRESHOLD
from app.models.brand import Brand
from app.models.org import Org
from app.models.plan import OrgMonthlyUsage
from app.models.prompt import PromptSet


def get_billing_period(org: Org, reference_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    Calculate the current billing period for an organization.
    
    The billing period starts on the billing_cycle_anchor day of each month
    and runs for exactly one month from that date.
    
    Args:
        org: Organization with billing_cycle_anchor
        reference_date: Date to calculate period for (defaults to now)
        
    Returns:
        Tuple of (period_start, period_end)
        
    Example:
        If billing_cycle_anchor = 15 (purchased on Nov 15):
        - Period: Nov 15 00:00:00 to Dec 15 00:00:00
        - Next period: Dec 15 00:00:00 to Jan 15 00:00:00
    """
    if reference_date is None:
        reference_date = datetime.utcnow()
    
    anchor_day = org.billing_cycle_anchor
    
    # Start with the anchor day in the current month
    try:
        period_start = reference_date.replace(
            day=anchor_day,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
    except ValueError:
        # Handle months that don't have the anchor day (e.g., Feb 30)
        # Use the last day of the month instead
        next_month = reference_date.replace(day=1) + relativedelta(months=1)
        period_start = (next_month - timedelta(days=1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
    
    # If we're before the anchor day this month, the period started last month
    if reference_date < period_start:
        period_start = period_start - relativedelta(months=1)
    
    # Period ends exactly one month later
    period_end = period_start + relativedelta(months=1)
    
    return period_start, period_end


def initialize_billing_period(org: Org, db: Session) -> None:
    """
    Initialize billing period for an organization.
    
    Sets current_period_start and current_period_end based on when
    they purchased their plan (or now if just created).
    
    Args:
        org: Organization to initialize
        db: Database session
    """
    if org.current_period_start is None:
        # Set billing cycle anchor to today's day of month
        now = datetime.utcnow()
        org.billing_cycle_anchor = now.day
        org.current_period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        org.current_period_end = org.current_period_start + relativedelta(months=1)
        db.commit()


def get_plan(org: Org) -> dict:
    """
    Get plan quotas for an organization.
    
    Args:
        org: Organization model
        
    Returns:
        Dictionary of quota limits for the plan
    """
    return PLAN_QUOTAS[org.plan_tier.value]


def get_or_create_usage(db: Session, org: Org, lock_for_update: bool = False) -> OrgMonthlyUsage:
    """
    Get or create usage record for org's current billing period.
    
    Args:
        db: Database session
        org: Organization
        lock_for_update: If True, locks the row with SELECT FOR UPDATE
        
    Returns:
        OrgMonthlyUsage record for current billing period
    """
    # Ensure org has billing period initialized
    initialize_billing_period(org, db)
    
    # Get current billing period
    period_start, period_end = get_billing_period(org)
    
    # Find or create usage record for this period
    query = db.query(OrgMonthlyUsage).filter(
        OrgMonthlyUsage.org_id == org.id,
        OrgMonthlyUsage.period_start == period_start
    )
    
    if lock_for_update:
        # Lock the row to prevent concurrent modifications
        query = query.with_for_update()
    
    usage = query.first()
    
    if not usage:
        usage = OrgMonthlyUsage(
            org_id=org.id,
            period_start=period_start,
            period_end=period_end,
            scans_used=0,
            prompts_used=0,
            ai_pages_generated=0,
        )
        db.add(usage)
        db.flush()  # Flush to get ID without committing
    
    return usage


def assert_within_limit(current: int, limit: Optional[int], resource: str) -> None:
    """
    Assert that current usage is within limit.
    
    Args:
        current: Current usage count
        limit: Quota limit (None means unlimited)
        resource: Resource name for error message
        
    Raises:
        HTTPException: 429 Too Many Requests if limit exceeded
    """
    from app.config import QUOTA_MESSAGES
    
    if limit is None:
        return  # Unlimited
    
    if current >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "LIMIT_EXCEEDED",
                "message": QUOTA_MESSAGES["LIMIT_EXCEEDED"].format(resource=resource),
                "resource": resource,
                "limit": limit,
                "current": current,
            },
        )


def check_warning(current: int, limit: Optional[int]) -> bool:
    """
    Check if usage is approaching limit (>= 80%).
    
    Args:
        current: Current usage count
        limit: Quota limit (None means unlimited)
        
    Returns:
        True if warning threshold reached
    """
    if limit is None:
        return False
    
    if limit == 0:
        return False
    
    return (current / limit) >= WARN_THRESHOLD


def get_usage_summary(db: Session, org: Org) -> dict:
    """
    Get usage summary for an organization's current billing period.
    
    Args:
        db: Database session
        org: Organization
        
    Returns:
        Dictionary with usage data, warnings, and billing period info
    """
    usage = get_or_create_usage(db, org)
    plan = get_plan(org)
    
    return {
        "scans": {
            "used": usage.scans_used,
            "limit": plan["scans"],
            "warn": check_warning(usage.scans_used, plan["scans"]),
        },
        "prompts": {
            "used": usage.prompts_used,
            "limit": plan["prompts"],
            "warn": check_warning(usage.prompts_used, plan["prompts"]),
        },
        "ai_pages": {
            "used": usage.ai_pages_generated,
            "limit": plan["ai_pages"],
            "warn": check_warning(usage.ai_pages_generated, plan["ai_pages"]),
        },
        "period_start": usage.period_start.isoformat(),
        "period_end": usage.period_end.isoformat(),
    }


def get_brand_count(db: Session, org_id: int) -> int:
    """Get count of brands for an organization."""
    return db.query(Brand).filter(Brand.org_id == org_id).count()


def get_prompt_count(db: Session, brand_id: int) -> int:
    """Get count of prompt sets for a brand."""
    return db.query(PromptSet).filter(PromptSet.brand_id == brand_id).count()

