"""Quota enforcement dependencies for FastAPI routes."""
from typing import Dict, Tuple

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.brand import Brand
from app.models.org import Org, OrgMember
from app.models.user import User
from app.services.quotas import (
    assert_within_limit,
    get_brand_count,
    get_or_create_usage,
    get_plan,
    get_prompt_count,
    get_usage_summary,
    month_anchor,
)


def require_brand_slot(
    org_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Check if organization can create another brand.
    
    Args:
        org_id: Organization ID
        db: Database session
        
    Returns:
        Usage info dict
        
    Raises:
        HTTPException: 429 Too Many Requests if brand limit exceeded
    """
    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    plan = get_plan(org)
    current_brands = get_brand_count(db, org_id)
    
    assert_within_limit(current_brands, plan["brands"], "Brand")
    
    return {
        "used": current_brands,
        "limit": plan["brands"],
    }


def require_prompt_slot(
    brand_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Check if brand can create another prompt set.
    
    Args:
        brand_id: Brand ID
        db: Database session
        
    Returns:
        Usage info dict
        
    Raises:
        HTTPException: 429 Too Many Requests if prompt limit exceeded
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )
    
    org = db.query(Org).filter(Org.id == brand.org_id).first()
    plan = get_plan(org)
    
    current_prompts = get_prompt_count(db, brand_id)
    
    assert_within_limit(current_prompts, plan["prompts"], "Prompt")
    
    return {
        "used": current_prompts,
        "limit": plan["prompts"],
    }


def require_scan_credit(
    org_id: int,
    model_name: str,
    db: Session = Depends(get_db),
) -> Tuple[Dict, int]:
    """
    Check if organization has scan credits available and reserve them.
    
    Uses SELECT FOR UPDATE to prevent double-spend under concurrent requests.
    
    Args:
        org_id: Organization ID
        model_name: Model name being used
        db: Database session
        
    Returns:
        Tuple of (usage info dict, credits to deduct)
        
    Raises:
        HTTPException: 429 if scan limit exceeded
    """
    from app.config import MODEL_WEIGHTS
    
    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    # Get credits needed based on model weight (default to 1 if not in config)
    credits_needed = MODEL_WEIGHTS.get(model_name, 1)
    # Fallback: check if "online" is in the name
    if credits_needed == 1 and "online" in model_name.lower():
        credits_needed = 2
    
    plan = get_plan(org)
    
    # Lock the usage row to prevent concurrent double-spend
    usage = get_or_create_usage(db, org, lock_for_update=True)
    
    # Check limit
    assert_within_limit(usage.scans_used + credits_needed, plan["scans"], "Scan")
    
    # Reserve the credits
    usage.scans_used += credits_needed
    db.commit()
    db.refresh(usage)
    
    return (
        {
            "used": usage.scans_used,
            "limit": plan["scans"],
        },
        credits_needed,
    )


def require_page_slot(
    org_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Check if organization can generate another AI page.
    
    Uses SELECT FOR UPDATE to prevent double-spend under concurrent requests.
    
    Args:
        org_id: Organization ID
        db: Database session
        
    Returns:
        Usage info dict
        
    Raises:
        HTTPException: 429 if page generation limit exceeded
    """
    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    plan = get_plan(org)
    
    # Lock the usage row to prevent concurrent double-spend
    usage = get_or_create_usage(db, org, lock_for_update=True)
    
    assert_within_limit(usage.ai_pages_generated, plan["ai_pages"], "AI page generation")
    
    # Reserve the slot
    usage.ai_pages_generated += 1
    db.commit()
    db.refresh(usage)
    
    return {
        "used": usage.ai_pages_generated,
        "limit": plan["ai_pages"],
    }


def check_seats_available(
    org_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Check if organization can add another seat/member.
    
    Args:
        org_id: Organization ID
        db: Database session
        
    Returns:
        Usage info dict
        
    Raises:
        HTTPException: 429 Too Many Requests if seat limit exceeded
    """
    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    plan = get_plan(org)
    current_seats = db.query(OrgMember).filter(OrgMember.org_id == org_id).count()
    
    assert_within_limit(current_seats, plan["seats"], "Seat")
    
    return {
        "used": current_seats,
        "limit": plan["seats"],
    }

