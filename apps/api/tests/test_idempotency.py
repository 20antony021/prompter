"""Tests for idempotency key handling."""
import pytest
from sqlalchemy.orm import Session

from app.services.job_queue import JobQueueService


class TestIdempotencyKeys:
    """Test idempotency key handling for job enqueuing."""

    def test_duplicate_scan_job_prevented(self, db: Session, redis_client):
        """Test that duplicate scan jobs are prevented by idempotency key."""
        job_service = JobQueueService(redis_conn=redis_client)
        
        scan_run_id = 123
        request_id = "test-request-123"
        
        # First enqueue should succeed
        job1 = job_service.enqueue_scan(
            scan_run_id=scan_run_id,
            request_id=request_id,
            user_id=1,
            org_id=1,
        )
        assert job1 is not None
        job1_id = job1.id
        
        # Second enqueue with same scan_run_id should be prevented
        job2 = job_service.enqueue_scan(
            scan_run_id=scan_run_id,
            request_id=request_id,
            user_id=1,
            org_id=1,
        )
        assert job2 is None  # Duplicate detected

    def test_custom_idempotency_key(self, db: Session, redis_client):
        """Test using custom idempotency keys."""
        job_service = JobQueueService(redis_conn=redis_client)
        
        custom_key = "custom-scan-key-456"
        
        # Enqueue with custom key
        job1 = job_service.enqueue_scan(
            scan_run_id=456,
            idempotency_key=custom_key,
            request_id="req-1",
            user_id=1,
            org_id=1,
        )
        assert job1 is not None
        
        # Different scan_run_id but same custom key should be prevented
        job2 = job_service.enqueue_scan(
            scan_run_id=789,  # Different ID
            idempotency_key=custom_key,  # Same key
            request_id="req-2",
            user_id=1,
            org_id=1,
        )
        assert job2 is None  # Duplicate detected

    def test_different_jobs_allowed(self, db: Session, redis_client):
        """Test that different jobs (different keys) are both allowed."""
        job_service = JobQueueService(redis_conn=redis_client)
        
        # Enqueue two different scans
        job1 = job_service.enqueue_scan(
            scan_run_id=100,
            request_id="req-1",
            user_id=1,
            org_id=1,
        )
        assert job1 is not None
        
        job2 = job_service.enqueue_scan(
            scan_run_id=200,  # Different scan
            request_id="req-2",
            user_id=1,
            org_id=1,
        )
        assert job2 is not None
        assert job1.id != job2.id

    def test_idempotency_key_expiration(self, db: Session, redis_client):
        """Test that idempotency keys expire after TTL."""
        import time
        
        job_service = JobQueueService(redis_conn=redis_client)
        
        # Enqueue with short TTL (would need to modify service for this test)
        scan_run_id = 999
        job1 = job_service.enqueue_scan(
            scan_run_id=scan_run_id,
            request_id="req-1",
            user_id=1,
            org_id=1,
        )
        assert job1 is not None
        
        # Manually expire the key for testing
        idempotency_key = f"scan:{scan_run_id}"
        redis_key = f"idempotency:{idempotency_key}"
        redis_client.expire(redis_key, 1)  # Expire in 1 second
        time.sleep(2)
        
        # Should be able to enqueue again after expiration
        job2 = job_service.enqueue_scan(
            scan_run_id=scan_run_id,
            request_id="req-2",
            user_id=1,
            org_id=1,
        )
        assert job2 is not None

    def test_page_generation_idempotency(self, db: Session, redis_client):
        """Test idempotency for page generation jobs."""
        job_service = JobQueueService(redis_conn=redis_client)
        
        page_id = 42
        urls = ["https://example.com"]
        
        # First enqueue should succeed
        job1 = job_service.enqueue_page_generation(
            page_id=page_id,
            urls_to_crawl=urls,
            request_id="req-1",
            user_id=1,
            org_id=1,
        )
        assert job1 is not None
        
        # Duplicate should be prevented
        job2 = job_service.enqueue_page_generation(
            page_id=page_id,
            urls_to_crawl=urls,
            request_id="req-2",
            user_id=1,
            org_id=1,
        )
        assert job2 is None

    def test_job_metadata_propagation(self, db: Session, redis_client):
        """Test that request context is propagated to job metadata."""
        job_service = JobQueueService(redis_conn=redis_client)
        
        # Enqueue with full context
        job = job_service.enqueue_scan(
            scan_run_id=777,
            request_id="test-request-id",
            user_id=123,
            org_id=456,
        )
        assert job is not None
        
        # Verify metadata
        assert job.meta["request_id"] == "test-request-id"
        assert job.meta["user_id"] == 123
        assert job.meta["org_id"] == 456
        assert job.meta["retry_count"] == 0
        assert "idempotency_key" in job.meta

