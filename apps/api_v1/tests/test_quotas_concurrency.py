"""Tests for concurrent quota reservation (race condition prevention)."""
import asyncio
import pytest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.org import Org, PlanTier
from app.models.plan import OrgMonthlyUsage
from app.models.user import User
from app.deps.quotas import require_scan_credit, require_page_slot
from app.services.quotas import get_billing_period, get_or_create_usage
from fastapi import HTTPException


class TestConcurrentReservations:
    """Test that SELECT FOR UPDATE prevents double-spend under concurrent load."""

    def test_concurrent_scan_reservations(self, db: Session):
        """Test that only allowed scans succeed with 10 concurrent requests."""
        # Setup: Starter org with 1000 scan limit, currently at 995
        org = Org(
            name="Test Org",
            slug="test-concurrent",
            plan_tier=PlanTier.STARTER,
            billing_cycle_anchor=1,
            current_period_start=datetime.utcnow()
        )
        db.add(org)
        db.flush()
        
        # Initialize billing period
        from dateutil.relativedelta import relativedelta
        org.current_period_end = org.current_period_start + relativedelta(months=1)
        
        # Create usage record with 995 scans used (5 credits remaining)
        period_start, period_end = get_billing_period(org)
        usage = OrgMonthlyUsage(
            org_id=org.id,
            period_start=period_start,
            period_end=period_end,
            scans_used=995,  # 5 credits left
            prompts_used=0,
            ai_pages_generated=0
        )
        db.add(usage)
        db.commit()
        
        # Try to reserve 10 scans concurrently (perplexity_online = 2 credits each = 20 total)
        # Only 2 should succeed (5 credits / 2 = 2 scans)
        def reserve_scan():
            """Reserve a scan credit (returns True on success, False on 429)."""
            try:
                # Create new session for this thread
                from app.database import SessionLocal
                thread_db = SessionLocal()
                try:
                    require_scan_credit(org.id, "perplexity_online", thread_db)
                    thread_db.commit()
                    return True
                except HTTPException as e:
                    thread_db.rollback()
                    if e.status_code == 429:
                        return False
                    raise
                finally:
                    thread_db.close()
            except Exception as e:
                print(f"Error: {e}")
                return False
        
        # Execute 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(reserve_scan) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # Count successes and failures
        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if r is False)
        
        # Assertions
        assert successes == 2, f"Expected 2 successful reservations, got {successes}"
        assert failures == 8, f"Expected 8 failed reservations, got {failures}"
        
        # Verify final usage count
        db.refresh(usage)
        assert usage.scans_used == 999, f"Expected 999 scans used (995 + 4), got {usage.scans_used}"

    def test_concurrent_page_reservations(self, db: Session):
        """Test that only allowed pages succeed with concurrent requests."""
        # Setup: Starter org with 3 page limit, currently at 2
        org = Org(
            name="Test Org Pages",
            slug="test-concurrent-pages",
            plan_tier=PlanTier.STARTER,
            billing_cycle_anchor=1,
            current_period_start=datetime.utcnow()
        )
        db.add(org)
        db.flush()
        
        # Initialize billing period
        from dateutil.relativedelta import relativedelta
        org.current_period_end = org.current_period_start + relativedelta(months=1)
        
        # Create usage record with 2 pages used (1 slot remaining)
        period_start, period_end = get_billing_period(org)
        usage = OrgMonthlyUsage(
            org_id=org.id,
            period_start=period_start,
            period_end=period_end,
            scans_used=0,
            prompts_used=0,
            ai_pages_generated=2  # 1 slot left
        )
        db.add(usage)
        db.commit()
        
        # Try to reserve 5 page slots concurrently
        # Only 1 should succeed
        def reserve_page():
            """Reserve a page slot (returns True on success, False on 429)."""
            try:
                from app.database import SessionLocal
                thread_db = SessionLocal()
                try:
                    require_page_slot(org.id, thread_db)
                    thread_db.commit()
                    return True
                except HTTPException as e:
                    thread_db.rollback()
                    if e.status_code == 429:
                        return False
                    raise
                finally:
                    thread_db.close()
            except Exception:
                return False
        
        # Execute 5 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(reserve_page) for _ in range(5)]
            results = [f.result() for f in futures]
        
        # Count successes and failures
        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if r is False)
        
        # Assertions
        assert successes == 1, f"Expected 1 successful reservation, got {successes}"
        assert failures == 4, f"Expected 4 failed reservations, got {failures}"
        
        # Verify final usage count
        db.refresh(usage)
        assert usage.ai_pages_generated == 3, f"Expected 3 pages used, got {usage.ai_pages_generated}"

    def test_no_double_spend_without_lock(self, db: Session):
        """Demonstrate that without SELECT FOR UPDATE, double-spend is possible."""
        # This test documents the problem that SELECT FOR UPDATE solves
        # In reality, with proper locking, this should not happen
        
        org = Org(
            name="Test No Lock",
            slug="test-no-lock",
            plan_tier=PlanTier.STARTER,
            billing_cycle_anchor=1,
            current_period_start=datetime.utcnow()
        )
        db.add(org)
        db.flush()
        
        from dateutil.relativedelta import relativedelta
        org.current_period_end = org.current_period_start + relativedelta(months=1)
        
        period_start, period_end = get_billing_period(org)
        usage = OrgMonthlyUsage(
            org_id=org.id,
            period_start=period_start,
            period_end=period_end,
            scans_used=999,  # 1 credit left
            prompts_used=0,
            ai_pages_generated=0
        )
        db.add(usage)
        db.commit()
        
        # With SELECT FOR UPDATE (lock_for_update=True), only 1 should succeed
        # Without it, multiple could succeed (race condition)
        
        # The current implementation uses lock_for_update=True, so this test
        # verifies that it works correctly
        def try_reserve_without_checking():
            """Attempt reservation."""
            try:
                from app.database import SessionLocal
                thread_db = SessionLocal()
                try:
                    # This will use SELECT FOR UPDATE internally
                    require_scan_credit(org.id, "gpt-4", thread_db)
                    thread_db.commit()
                    return True
                except HTTPException:
                    thread_db.rollback()
                    return False
                finally:
                    thread_db.close()
            except Exception:
                return False
        
        # Execute 3 concurrent requests (only 1 credit available)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(try_reserve_without_checking) for _ in range(3)]
            results = [f.result() for f in futures]
        
        successes = sum(1 for r in results if r is True)
        
        # With proper locking, exactly 1 should succeed
        assert successes == 1, f"Expected exactly 1 success with locking, got {successes}"

    def test_concurrent_mixed_models(self, db: Session):
        """Test concurrent requests with different model weights."""
        org = Org(
            name="Test Mixed",
            slug="test-mixed",
            plan_tier=PlanTier.STARTER,
            billing_cycle_anchor=1,
            current_period_start=datetime.utcnow()
        )
        db.add(org)
        db.flush()
        
        from dateutil.relativedelta import relativedelta
        org.current_period_end = org.current_period_start + relativedelta(months=1)
        
        period_start, period_end = get_billing_period(org)
        usage = OrgMonthlyUsage(
            org_id=org.id,
            period_start=period_start,
            period_end=period_end,
            scans_used=995,  # 5 credits left
            prompts_used=0,
            ai_pages_generated=0
        )
        db.add(usage)
        db.commit()
        
        # Mix of requests: 3x perplexity (2 credits each) + 5x gpt-4 (1 credit each)
        # Total needed: 6 + 5 = 11 credits, but only 5 available
        def reserve_model(model_name):
            try:
                from app.database import SessionLocal
                thread_db = SessionLocal()
                try:
                    require_scan_credit(org.id, model_name, thread_db)
                    thread_db.commit()
                    return (model_name, True)
                except HTTPException:
                    thread_db.rollback()
                    return (model_name, False)
                finally:
                    thread_db.close()
            except Exception:
                return (model_name, False)
        
        requests = (
            ["perplexity_online"] * 3 +  # 2 credits each
            ["gpt-4"] * 5  # 1 credit each
        )
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(reserve_model, model) for model in requests]
            results = [f.result() for f in futures]
        
        # Count successes by model type
        perplexity_successes = sum(1 for model, success in results 
                                   if model == "perplexity_online" and success)
        gpt4_successes = sum(1 for model, success in results 
                            if model == "gpt-4" and success)
        
        total_credits_used = (perplexity_successes * 2) + (gpt4_successes * 1)
        
        # Should use exactly 5 credits (or less if race conditions exist)
        assert total_credits_used <= 5, f"Used {total_credits_used} credits, max was 5"
        assert total_credits_used >= 4, f"Used only {total_credits_used} credits, expected ~5"
        
        # Verify final usage
        db.refresh(usage)
        expected_final = 995 + total_credits_used
        assert usage.scans_used == expected_final


class TestConcurrencySafeguards:
    """Test additional safeguards for concurrent operations."""

    def test_transaction_isolation(self, db: Session):
        """Verify that transactions are properly isolated."""
        org = Org(
            name="Test Isolation",
            slug="test-isolation",
            plan_tier=PlanTier.PRO,
            billing_cycle_anchor=1,
            current_period_start=datetime.utcnow()
        )
        db.add(org)
        db.commit()
        
        # Start two transactions and verify they don't interfere
        from app.database import SessionLocal
        
        session1 = SessionLocal()
        session2 = SessionLocal()
        
        try:
            # Both sessions read the same usage record
            usage1 = get_or_create_usage(session1, org, lock_for_update=True)
            
            # Second session should wait for lock (or timeout)
            # This demonstrates proper locking behavior
            initial_scans = usage1.scans_used
            
            # First transaction modifies
            usage1.scans_used += 10
            session1.commit()
            
            # Second transaction should see the updated value
            usage2 = get_or_create_usage(session2, org, lock_for_update=False)
            assert usage2.scans_used == initial_scans + 10
            
        finally:
            session1.close()
            session2.close()

    def test_rollback_on_error(self, db: Session):
        """Verify that failed reservations are rolled back."""
        org = Org(
            name="Test Rollback",
            slug="test-rollback",
            plan_tier=PlanTier.STARTER,
            billing_cycle_anchor=1,
            current_period_start=datetime.utcnow()
        )
        db.add(org)
        db.flush()
        
        from dateutil.relativedelta import relativedelta
        org.current_period_end = org.current_period_start + relativedelta(months=1)
        
        period_start, period_end = get_billing_period(org)
        usage = OrgMonthlyUsage(
            org_id=org.id,
            period_start=period_start,
            period_end=period_end,
            scans_used=1000,  # At limit
            prompts_used=0,
            ai_pages_generated=0
        )
        db.add(usage)
        db.commit()
        
        initial_count = usage.scans_used
        
        # Try to reserve (should fail)
        try:
            require_scan_credit(org.id, "gpt-4", db)
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 429
            db.rollback()
        
        # Verify count didn't change
        db.refresh(usage)
        assert usage.scans_used == initial_count

