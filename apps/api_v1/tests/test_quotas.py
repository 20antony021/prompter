"""Tests for quota enforcement and limits."""
import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.brand import Brand
from app.models.knowledge_page import KnowledgePage, PageStatus
from app.models.org import Org, OrgMember, OrgRole, PlanTier
from app.models.plan import OrgMonthlyUsage
from app.models.prompt import PromptSet
from app.models.scan import ScanRun, ScanResult, ScanStatus
from app.models.user import User
from app.services.quotas import (
    assert_within_limit,
    check_warning,
    get_or_create_usage,
    get_plan,
    get_brand_count,
    get_prompt_count,
    month_anchor,
)
from app.config import PLAN_QUOTAS, WARN_THRESHOLD


class TestQuotaHelpers:
    """Test quota helper functions."""

    def test_month_anchor(self):
        """Test month anchor returns first day of month."""
        test_date = date(2025, 11, 15)
        anchor = month_anchor(test_date)
        assert anchor == date(2025, 11, 1)
        
        # Test with None (should use today)
        anchor_today = month_anchor()
        assert anchor_today.day == 1

    def test_get_plan(self, db: Session):
        """Test getting plan quotas for an org."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        db.add(org)
        db.commit()
        
        plan = get_plan(org)
        assert plan == PLAN_QUOTAS["starter"]
        assert plan["brands"] == 1
        assert plan["scans"] == 1000

    def test_assert_within_limit_pass(self):
        """Test assert_within_limit passes when under limit."""
        # Should not raise
        assert_within_limit(5, 10, "Test")

    def test_assert_within_limit_fail(self):
        """Test assert_within_limit raises when at or over limit."""
        with pytest.raises(HTTPException) as exc_info:
            assert_within_limit(10, 10, "Test")
        
        assert exc_info.value.status_code == 402
        assert "LIMIT_EXCEEDED" in str(exc_info.value.detail)

    def test_assert_within_limit_unlimited(self):
        """Test assert_within_limit passes when limit is None (unlimited)."""
        # Should not raise
        assert_within_limit(1000000, None, "Test")

    def test_check_warning(self):
        """Test warning threshold detection."""
        # Below threshold
        assert not check_warning(7, 10)  # 70%
        
        # At threshold
        assert check_warning(8, 10)  # 80%
        
        # Above threshold
        assert check_warning(9, 10)  # 90%
        
        # Unlimited
        assert not check_warning(1000, None)


class TestBrandQuota:
    """Test brand quota enforcement."""

    def test_brand_limit_starter(self, db: Session):
        """Test starter plan can only create 1 brand."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        db.add(org)
        db.commit()
        
        # Create first brand - should succeed
        brand1 = Brand(org_id=org.id, name="Brand 1", website="https://example.com")
        db.add(brand1)
        db.commit()
        
        count = get_brand_count(db, org.id)
        assert count == 1
        
        # Try to create second brand - should fail
        plan = get_plan(org)
        with pytest.raises(HTTPException) as exc_info:
            assert_within_limit(count, plan["brands"], "Brand")
        
        assert exc_info.value.status_code == 402

    def test_brand_limit_pro(self, db: Session):
        """Test pro plan can create up to 3 brands."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.PRO)
        db.add(org)
        db.commit()
        
        # Create 3 brands - should succeed
        for i in range(3):
            brand = Brand(org_id=org.id, name=f"Brand {i+1}", website="https://example.com")
            db.add(brand)
        db.commit()
        
        count = get_brand_count(db, org.id)
        assert count == 3
        
        # Try to create 4th brand - should fail
        plan = get_plan(org)
        with pytest.raises(HTTPException):
            assert_within_limit(count, plan["brands"], "Brand")


class TestScanQuota:
    """Test scan quota enforcement."""

    def test_scan_limit_enforcement(self, db: Session):
        """Test scan limit is enforced correctly."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        db.add(org)
        db.commit()
        
        month = month_anchor()
        usage = get_or_create_usage(db, org.id, month)
        
        # Use up all scans
        usage.scans_used = 1000
        db.commit()
        
        plan = get_plan(org)
        
        # Try to use one more - should fail
        with pytest.raises(HTTPException) as exc_info:
            assert_within_limit(usage.scans_used, plan["scans"], "Scan")
        
        assert exc_info.value.status_code == 402

    def test_perplexity_counts_double(self, db: Session):
        """Test Perplexity online models count as 2 scans."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        db.add(org)
        db.commit()
        
        month = month_anchor()
        usage = get_or_create_usage(db, org.id, month)
        plan = get_plan(org)
        
        # Simulate perplexity online scan (costs 2 credits)
        model_name = "perplexity_sonar_large_online"
        credits_needed = 2 if "perplexity" in model_name.lower() and "online" in model_name.lower() else 1
        
        assert credits_needed == 2
        
        # Should be able to reserve credits
        usage.scans_used += credits_needed
        db.commit()
        
        assert usage.scans_used == 2


class TestPageQuota:
    """Test AI page generation quota."""

    def test_page_limit_starter(self, db: Session):
        """Test starter plan can generate 3 pages per month."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        brand = Brand(org_id=org.id, name="Brand", website="https://example.com")
        db.add_all([org, brand])
        db.commit()
        
        month = month_anchor()
        usage = get_or_create_usage(db, org.id, month)
        
        # Generate 3 pages
        usage.ai_pages_generated = 3
        db.commit()
        
        plan = get_plan(org)
        
        # Try to generate 4th page - should fail
        with pytest.raises(HTTPException):
            assert_within_limit(usage.ai_pages_generated, plan["ai_pages"], "AI page generation")


class TestPromptQuota:
    """Test prompt quota enforcement."""

    def test_prompt_limit_starter(self, db: Session):
        """Test starter plan can create 30 prompts."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        brand = Brand(org_id=org.id, name="Brand", website="https://example.com")
        db.add_all([org, brand])
        db.commit()
        
        # Create 30 prompt sets
        for i in range(30):
            prompt_set = PromptSet(brand_id=brand.id, name=f"Prompt Set {i+1}")
            db.add(prompt_set)
        db.commit()
        
        count = get_prompt_count(db, brand.id)
        assert count == 30
        
        plan = get_plan(org)
        
        # Try to create 31st - should fail
        with pytest.raises(HTTPException):
            assert_within_limit(count, plan["prompts"], "Prompt")


class TestSeatsQuota:
    """Test seats/member quota enforcement."""

    def test_seats_limit_starter(self, db: Session):
        """Test starter plan allows 3 seats."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        db.add(org)
        db.commit()
        
        # Add 3 members
        for i in range(3):
            user = User(
                auth_provider_id=f"user{i}",
                email=f"user{i}@example.com",
                name=f"User {i}"
            )
            db.add(user)
            db.flush()
            
            member = OrgMember(org_id=org.id, user_id=user.id, role=OrgRole.MEMBER)
            db.add(member)
        db.commit()
        
        current_seats = db.query(OrgMember).filter(OrgMember.org_id == org.id).count()
        assert current_seats == 3
        
        plan = get_plan(org)
        
        # Try to add 4th member - should fail
        with pytest.raises(HTTPException):
            assert_within_limit(current_seats, plan["seats"], "Seat")

    def test_seats_unlimited_business(self, db: Session):
        """Test business plan has unlimited seats."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.BUSINESS)
        db.add(org)
        db.commit()
        
        plan = get_plan(org)
        assert plan["seats"] is None  # Unlimited
        
        # Should be able to add many members
        for i in range(100):
            user = User(
                auth_provider_id=f"user{i}",
                email=f"user{i}@example.com",
                name=f"User {i}"
            )
            db.add(user)
            db.flush()
            
            member = OrgMember(org_id=org.id, user_id=user.id, role=OrgRole.MEMBER)
            db.add(member)
        db.commit()
        
        current_seats = db.query(OrgMember).filter(OrgMember.org_id == org.id).count()
        
        # Should not raise
        assert_within_limit(current_seats, plan["seats"], "Seat")


class TestRetentionPolicy:
    """Test data retention enforcement."""

    def test_retention_days_starter(self, db: Session):
        """Test starter plan retains data for 30 days."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        brand = Brand(org_id=org.id, name="Brand", website="https://example.com")
        db.add_all([org, brand])
        db.commit()
        
        plan = get_plan(org)
        retention_days = plan["retention_days"]
        assert retention_days == 30
        
        # Create old scan run
        old_scan = ScanRun(
            brand_id=brand.id,
            status=ScanStatus.DONE,
            model_matrix_json=["gpt-4"],
            created_at=datetime.utcnow() - timedelta(days=35)
        )
        db.add(old_scan)
        db.commit()
        
        # Check if scan should be deleted
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        assert old_scan.created_at < cutoff_date

    def test_retention_unlimited_enterprise(self, db: Session):
        """Test enterprise plan has unlimited retention."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.ENTERPRISE)
        db.add(org)
        db.commit()
        
        plan = get_plan(org)
        assert plan["retention_days"] is None  # Unlimited


class TestUsageWarnings:
    """Test 80% warning thresholds."""

    def test_warning_at_80_percent(self, db: Session):
        """Test warning flag is set at 80% usage."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        db.add(org)
        db.commit()
        
        month = month_anchor()
        usage = get_or_create_usage(db, org.id, month)
        
        # Use 80% of scans (800 out of 1000)
        usage.scans_used = 800
        db.commit()
        
        plan = get_plan(org)
        warn = check_warning(usage.scans_used, plan["scans"])
        assert warn is True

    def test_no_warning_below_80_percent(self, db: Session):
        """Test no warning below 80% usage."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        db.add(org)
        db.commit()
        
        month = month_anchor()
        usage = get_or_create_usage(db, org.id, month)
        
        # Use 70% of scans (700 out of 1000)
        usage.scans_used = 700
        db.commit()
        
        plan = get_plan(org)
        warn = check_warning(usage.scans_used, plan["scans"])
        assert warn is False


class TestPlanUpgrades:
    """Test different plan tier quotas."""

    def test_starter_quotas(self, db: Session):
        """Test all starter plan quotas."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
        db.add(org)
        db.commit()
        
        plan = get_plan(org)
        assert plan["brands"] == 1
        assert plan["prompts"] == 30
        assert plan["scans"] == 1000
        assert plan["ai_pages"] == 3
        assert plan["seats"] == 3
        assert plan["retention_days"] == 30

    def test_pro_quotas(self, db: Session):
        """Test all pro plan quotas."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.PRO)
        db.add(org)
        db.commit()
        
        plan = get_plan(org)
        assert plan["brands"] == 3
        assert plan["prompts"] == 150
        assert plan["scans"] == 5000
        assert plan["ai_pages"] == 10
        assert plan["seats"] == 10
        assert plan["retention_days"] == 180

    def test_business_quotas(self, db: Session):
        """Test all business plan quotas."""
        org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.BUSINESS)
        db.add(org)
        db.commit()
        
        plan = get_plan(org)
        assert plan["brands"] == 10
        assert plan["prompts"] == 500
        assert plan["scans"] == 15000
        assert plan["ai_pages"] == 25
        assert plan["seats"] is None  # Unlimited
        assert plan["retention_days"] == 365

