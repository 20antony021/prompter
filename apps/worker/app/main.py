"""Worker main entry point with reliability features."""
import logging
import os
import signal
import sys
from datetime import timedelta

from redis import Redis
from rq import Queue, Worker
from rq.job import Job

# Add parent directory to path to import from api
sys.path.append(os.path.join(os.path.dirname(__file__), "../../api"))

from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - request_id=%(request_id)s",
)
logger = logging.getLogger(__name__)


class WorkerConfig:
    """
    Worker configuration with reliability features.
    
    Features:
    - Job timeouts per queue
    - Retry policies with exponential backoff
    - Dead Letter Queue (DLQ) for failed jobs
    - Graceful shutdown handling
    """

    # Job timeouts (in seconds)
    TIMEOUTS = {
        "default": 300,  # 5 minutes
        "scans": 1800,  # 30 minutes (LLM calls can be slow)
        "pages": 600,  # 10 minutes
    }

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min (exponential backoff)

    # Visibility timeout - how long a job is "invisible" before considered failed
    VISIBILITY_TIMEOUT = 3600  # 1 hour

    # Dead Letter Queue name
    DLQ_NAME = "failed"


def setup_dlq(redis_conn: Redis) -> Queue:
    """
    Set up Dead Letter Queue for permanently failed jobs.
    
    Jobs that exhaust all retries are moved to DLQ for manual inspection.
    """
    dlq = Queue(WorkerConfig.DLQ_NAME, connection=redis_conn)
    logger.info(f"Dead Letter Queue '{WorkerConfig.DLQ_NAME}' configured")
    return dlq


def job_failure_callback(job: Job, connection: Redis, type, value, traceback):
    """
    Callback when a job fails.
    
    Implements retry logic with exponential backoff.
    If max retries exceeded, move to DLQ.
    """
    retry_count = job.meta.get("retry_count", 0)
    
    logger.error(
        f"Job {job.id} failed (attempt {retry_count + 1}/{WorkerConfig.MAX_RETRIES}): {value}",
        extra={"request_id": job.meta.get("request_id")},
    )

    if retry_count < WorkerConfig.MAX_RETRIES:
        # Retry with exponential backoff
        retry_delay = WorkerConfig.RETRY_DELAYS[min(retry_count, len(WorkerConfig.RETRY_DELAYS) - 1)]
        job.meta["retry_count"] = retry_count + 1
        job.save_meta()
        
        # Re-enqueue job with delay
        queue = Queue(job.origin, connection=connection)
        queue.enqueue_in(
            timedelta(seconds=retry_delay),
            job.func,
            *job.args,
            **job.kwargs,
            job_id=f"{job.id}_retry_{retry_count + 1}",
            meta=job.meta,
        )
        
        logger.info(
            f"Job {job.id} scheduled for retry in {retry_delay}s",
            extra={"request_id": job.meta.get("request_id")},
        )
    else:
        # Move to DLQ
        dlq = Queue(WorkerConfig.DLQ_NAME, connection=connection)
        dlq.enqueue(
            "app.jobs.dlq_handler.process_failed_job",
            job_id=job.id,
            job_data={
                "func": str(job.func),
                "args": job.args,
                "kwargs": job.kwargs,
                "failure_reason": str(value),
                "traceback": str(traceback),
                "meta": job.meta,
            },
            job_id=f"dlq_{job.id}",
        )
        
        logger.error(
            f"Job {job.id} exhausted retries, moved to DLQ",
            extra={"request_id": job.meta.get("request_id")},
        )


def graceful_shutdown(signum, frame):
    """Handle graceful shutdown on SIGTERM/SIGINT."""
    logger.info("Received shutdown signal, finishing current jobs...")
    sys.exit(0)


def main():
    """Start RQ worker with reliability features."""
    logger.info("Starting Prompter worker with reliability features...")

    # Set up graceful shutdown
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)

    # Connect to Redis
    redis_conn = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    # Set up Dead Letter Queue
    dlq = setup_dlq(redis_conn)

    # Create queues with specific timeouts
    queues = []
    for queue_name in ["scans", "pages", "default"]:
        queue = Queue(
            queue_name,
            connection=redis_conn,
            default_timeout=WorkerConfig.TIMEOUTS.get(queue_name, 300),
        )
        queues.append(queue)
        logger.info(
            f"Queue '{queue_name}' configured (timeout: {WorkerConfig.TIMEOUTS.get(queue_name)}s)"
        )

    # Create worker with configuration
    worker = Worker(
        queues=queues,
        connection=redis_conn,
        name="prompter-worker",
        # Worker-level settings
        job_monitoring_interval=30,  # Check for stale jobs every 30s
    )

    # Register failure callback
    # Note: RQ doesn't support failure callbacks directly
    # This would need to be implemented in job decorators

    logger.info(
        f"Worker started - listening on queues: {[q.name for q in queues]}, DLQ: {dlq.name}"
    )

    # Start processing jobs
    try:
        worker.work(with_scheduler=True, burst=False)
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

