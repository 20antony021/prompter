"""Job queue service with idempotency support."""
import hashlib
import logging
from typing import Any, Dict, Optional

from redis import Redis
from rq import Queue
from rq.job import Job

from app.config import settings

logger = logging.getLogger(__name__)


class JobQueueService:
    """
    Service for enqueuing background jobs with reliability features.
    
    Features:
    - Idempotency keys to prevent duplicate job execution
    - Job metadata propagation (request_id, user_id, org_id)
    - Configurable timeouts and retries
    """

    def __init__(self, redis_conn: Optional[Redis] = None):
        """Initialize job queue service."""
        if redis_conn is None:
            self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        else:
            self.redis = redis_conn

    def enqueue_scan(
        self,
        scan_run_id: int,
        idempotency_key: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        org_id: Optional[int] = None,
    ) -> Optional[Job]:
        """
        Enqueue a scan job with idempotency.
        
        Args:
            scan_run_id: ID of scan run to execute
            idempotency_key: Optional idempotency key (defaults to f"scan:{scan_run_id}")
            request_id: Request ID for tracing
            user_id: User who initiated the scan
            org_id: Organization ID for context
        
        Returns:
            Job object if enqueued, None if duplicate
        """
        # Generate idempotency key if not provided
        if idempotency_key is None:
            idempotency_key = f"scan:{scan_run_id}"

        # Check if job already exists
        if self._check_idempotency(idempotency_key):
            logger.info(
                f"Duplicate scan job detected: {idempotency_key}",
                extra={"request_id": request_id, "scan_run_id": scan_run_id},
            )
            return None

        # Enqueue job
        queue = Queue("scans", connection=self.redis)
        job = queue.enqueue(
            "app.jobs.scan_executor.execute_scan_run",
            scan_run_id,
            job_id=self._generate_job_id(idempotency_key),
            meta={
                "idempotency_key": idempotency_key,
                "request_id": request_id,
                "user_id": user_id,
                "org_id": org_id,
                "retry_count": 0,
            },
            timeout="30m",  # 30 minute timeout
        )

        # Store idempotency key
        self._store_idempotency(idempotency_key, job.id)

        logger.info(
            f"Scan job enqueued: {job.id} (scan_run_id={scan_run_id})",
            extra={"request_id": request_id, "job_id": job.id},
        )

        return job

    def enqueue_page_generation(
        self,
        page_id: int,
        urls_to_crawl: list[str],
        idempotency_key: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        org_id: Optional[int] = None,
    ) -> Optional[Job]:
        """
        Enqueue a page generation job with idempotency.
        
        Args:
            page_id: ID of knowledge page to generate
            urls_to_crawl: List of URLs to crawl for content
            idempotency_key: Optional idempotency key
            request_id: Request ID for tracing
            user_id: User who initiated generation
            org_id: Organization ID for context
        
        Returns:
            Job object if enqueued, None if duplicate
        """
        # Generate idempotency key if not provided
        if idempotency_key is None:
            idempotency_key = f"page_gen:{page_id}"

        # Check if job already exists
        if self._check_idempotency(idempotency_key):
            logger.info(
                f"Duplicate page generation job detected: {idempotency_key}",
                extra={"request_id": request_id, "page_id": page_id},
            )
            return None

        # Enqueue job
        queue = Queue("pages", connection=self.redis)
        job = queue.enqueue(
            "app.jobs.page_generator_job.generate_page_content",
            page_id,
            urls_to_crawl,
            job_id=self._generate_job_id(idempotency_key),
            meta={
                "idempotency_key": idempotency_key,
                "request_id": request_id,
                "user_id": user_id,
                "org_id": org_id,
                "retry_count": 0,
            },
            timeout="10m",  # 10 minute timeout
        )

        # Store idempotency key
        self._store_idempotency(idempotency_key, job.id)

        logger.info(
            f"Page generation job enqueued: {job.id} (page_id={page_id})",
            extra={"request_id": request_id, "job_id": job.id},
        )

        return job

    def _check_idempotency(self, idempotency_key: str) -> bool:
        """
        Check if a job with this idempotency key already exists.
        
        Returns:
            True if duplicate, False if new
        """
        redis_key = f"idempotency:{idempotency_key}"
        return self.redis.exists(redis_key) > 0

    def _store_idempotency(self, idempotency_key: str, job_id: str, ttl: int = 86400):
        """
        Store idempotency key in Redis.
        
        Args:
            idempotency_key: Idempotency key
            job_id: Job ID
            ttl: Time-to-live in seconds (default: 24 hours)
        """
        redis_key = f"idempotency:{idempotency_key}"
        self.redis.setex(redis_key, ttl, job_id)

    def _generate_job_id(self, idempotency_key: str) -> str:
        """
        Generate deterministic job ID from idempotency key.
        
        This ensures the same idempotency key always generates the same job ID.
        """
        return hashlib.sha256(idempotency_key.encode()).hexdigest()[:16]

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a job by ID.
        
        Returns:
            Job status dict or None if not found
        """
        try:
            job = Job.fetch(job_id, connection=self.redis)
            return {
                "id": job.id,
                "status": job.get_status(),
                "created_at": job.created_at,
                "started_at": job.started_at,
                "ended_at": job.ended_at,
                "result": job.result,
                "meta": job.meta,
            }
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id}: {e}")
            return None

