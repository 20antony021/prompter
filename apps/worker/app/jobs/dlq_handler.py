"""Dead Letter Queue handler for permanently failed jobs."""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def process_failed_job(job_id: str, job_data: Dict[str, Any]):
    """
    Process a job that has been moved to the Dead Letter Queue.
    
    This job records the failure for monitoring/alerting and
    stores it for manual inspection.
    
    Args:
        job_id: Original job ID
        job_data: Job data including function, args, kwargs, and failure info
    """
    logger.error(
        f"DLQ: Processing permanently failed job {job_id}",
        extra={
            "job_id": job_id,
            "func": job_data.get("func"),
            "failure_reason": job_data.get("failure_reason"),
            "retry_count": job_data.get("meta", {}).get("retry_count", 0),
        },
    )

    # In production, you would:
    # 1. Store in a failures table for inspection
    # 2. Send alert to monitoring system (Sentry, PagerDuty, etc.)
    # 3. Emit metrics for tracking failure rate
    
    # Example: Send to Sentry
    try:
        import sentry_sdk
        sentry_sdk.capture_message(
            f"Job failed permanently: {job_id}",
            level="error",
            extras={
                "job_id": job_id,
                "job_data": job_data,
            },
        )
    except Exception:
        pass  # Sentry not configured

    # TODO: Store in database for manual retry/inspection
    # from app.models.failed_jobs import FailedJob
    # failed_job = FailedJob(
    #     job_id=job_id,
    #     func_name=job_data["func"],
    #     args_json=job_data["args"],
    #     kwargs_json=job_data["kwargs"],
    #     failure_reason=job_data["failure_reason"],
    #     traceback=job_data["traceback"],
    # )
    # db.add(failed_job)
    # db.commit()

    logger.info(f"DLQ: Job {job_id} processed and logged")

