"""Retention sweeper job - deletes old data based on plan retention policies.

Safety features:
- Caps deletions per run to prevent long transactions
- Logs detailed counts per org
- Skips orgs with NULL retention_days (unlimited/enterprise)
- Handles errors per org without failing entire job
"""
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.config import PLAN_QUOTAS
from app.database import get_db
from app.models.org import Org
from app.models.scan import ScanRun, ScanResult
from app.models.mention import Mention

logger = logging.getLogger(__name__)

# Safety: cap deletions per run to avoid long transactions
# If more items need deletion, they'll be picked up in the next run
MAX_DELETIONS_PER_ORG = 5000
MAX_DELETIONS_PER_RUN = 50000


def delete_old_scans(db: Session, org: Org, retention_days: int, max_deletions: int = MAX_DELETIONS_PER_ORG) -> dict:
    """
    Delete scan runs and related data older than retention period.
    
    Caps deletions to prevent long transactions. If more items need deletion,
    they'll be picked up in the next run.
    
    Args:
        db: Database session
        org: Organization
        retention_days: Number of days to retain data
        max_deletions: Maximum number of scan runs to delete per call
        
    Returns:
        Dictionary with deletion counts: {
            "scans_deleted": int,
            "results_deleted": int,
            "mentions_deleted": int,
            "capped": bool (True if more items remain to delete)
        }
    """
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    # Count total items before deletion for logging
    total_old_scans = (
        db.query(ScanRun)
        .join(ScanRun.brand)
        .filter(
            ScanRun.brand.has(org_id=org.id),
            ScanRun.created_at < cutoff_date,
        )
        .count()
    )
    
    if total_old_scans == 0:
        logger.debug(f"Org {org.id}: No old scans to delete")
        return {
            "scans_deleted": 0,
            "results_deleted": 0,
            "mentions_deleted": 0,
            "capped": False,
        }
    
    # Get scan runs to delete (limited by max_deletions)
    old_scan_runs = (
        db.query(ScanRun)
        .join(ScanRun.brand)
        .filter(
            ScanRun.brand.has(org_id=org.id),
            ScanRun.created_at < cutoff_date,
        )
        .order_by(ScanRun.created_at.asc())  # Delete oldest first
        .limit(max_deletions)
        .all()
    )
    
    scans_deleted = 0
    results_deleted = 0
    mentions_deleted = 0
    
    logger.info(
        f"Org {org.id}: Deleting {len(old_scan_runs)} of {total_old_scans} old scan runs "
        f"(cutoff: {cutoff_date.isoformat()})"
    )
    
    for scan_run in old_scan_runs:
        # Count and delete related mentions
        mention_count = db.query(Mention).filter(
            Mention.scan_result.has(scan_run_id=scan_run.id)
        ).count()
        db.query(Mention).filter(
            Mention.scan_result.has(scan_run_id=scan_run.id)
        ).delete(synchronize_session=False)
        mentions_deleted += mention_count
        
        # Count and delete scan results
        result_count = db.query(ScanResult).filter(
            ScanResult.scan_run_id == scan_run.id
        ).count()
        db.query(ScanResult).filter(
            ScanResult.scan_run_id == scan_run.id
        ).delete(synchronize_session=False)
        results_deleted += result_count
        
        # Delete scan run
        db.delete(scan_run)
        scans_deleted += 1
    
    db.commit()
    
    capped = total_old_scans > max_deletions
    if capped:
        logger.warning(
            f"Org {org.id}: Deletion capped at {max_deletions} scan runs. "
            f"{total_old_scans - max_deletions} items remain for next run."
        )
    
    logger.info(
        f"Org {org.id}: Deleted {scans_deleted} scans, {results_deleted} results, {mentions_deleted} mentions"
    )
    
    return {
        "scans_deleted": scans_deleted,
        "results_deleted": results_deleted,
        "mentions_deleted": mentions_deleted,
        "capped": capped,
    }


def sweep_retention_for_org(db: Session, org: Org) -> dict:
    """
    Sweep retention for a single organization.
    
    Args:
        db: Database session
        org: Organization
        
    Returns:
        Dictionary with sweep results including detailed counts
    """
    plan = PLAN_QUOTAS[org.plan_tier.value]
    retention_days = plan.get("retention_days")
    
    # Safety: Skip orgs with NULL retention_days (unlimited/enterprise)
    if retention_days is None:
        logger.info(f"Org {org.id} ({org.name}) has unlimited retention (plan={org.plan_tier.value}), skipping")
        return {
            "org_id": org.id,
            "org_name": org.name,
            "plan_tier": org.plan_tier.value,
            "retention_days": None,
            "scans_deleted": 0,
            "results_deleted": 0,
            "mentions_deleted": 0,
            "skipped": True,
            "capped": False,
        }
    
    logger.info(
        f"Sweeping retention for org {org.id} ({org.name}), "
        f"plan={org.plan_tier.value}, retention={retention_days} days"
    )
    
    deletion_result = delete_old_scans(db, org, retention_days)
    
    logger.info(
        f"Completed retention sweep for org {org.id}: "
        f"{deletion_result['scans_deleted']} scans, "
        f"{deletion_result['results_deleted']} results, "
        f"{deletion_result['mentions_deleted']} mentions deleted"
        + (" (capped - more items remain)" if deletion_result['capped'] else "")
    )
    
    return {
        "org_id": org.id,
        "org_name": org.name,
        "plan_tier": org.plan_tier.value,
        "retention_days": retention_days,
        "scans_deleted": deletion_result["scans_deleted"],
        "results_deleted": deletion_result["results_deleted"],
        "mentions_deleted": deletion_result["mentions_deleted"],
        "capped": deletion_result["capped"],
        "skipped": False,
    }


def run_retention_sweeper():
    """
    Run retention sweeper for all organizations.
    
    This job should be run daily via cron/scheduler (e.g., 02:00 UTC).
    
    Safety features:
    - Caps deletions per org and per run to prevent long transactions
    - Logs detailed counts for monitoring
    - Skips orgs with unlimited retention (NULL retention_days)
    - Handles errors per org without failing entire job
    
    Returns:
        Dictionary with job results including detailed statistics
    """
    logger.info("=" * 80)
    logger.info("Starting retention sweeper job")
    logger.info(f"Max deletions per org: {MAX_DELETIONS_PER_ORG}")
    logger.info(f"Max deletions per run: {MAX_DELETIONS_PER_RUN}")
    logger.info("=" * 80)
    start_time = datetime.utcnow()
    
    db = next(get_db())
    
    try:
        # Get all organizations
        orgs = db.query(Org).all()
        logger.info(f"Found {len(orgs)} organizations to process")
        
        results = []
        total_scans_deleted = 0
        total_results_deleted = 0
        total_mentions_deleted = 0
        orgs_skipped = 0
        orgs_capped = 0
        orgs_with_errors = 0
        
        for org in orgs:
            # Safety: Check global cap
            if total_scans_deleted >= MAX_DELETIONS_PER_RUN:
                logger.warning(
                    f"Global deletion cap ({MAX_DELETIONS_PER_RUN}) reached. "
                    f"Stopping after {len(results)} orgs. Remaining orgs will be processed in next run."
                )
                break
            
            try:
                result = sweep_retention_for_org(db, org)
                results.append(result)
                
                if result.get("skipped"):
                    orgs_skipped += 1
                else:
                    total_scans_deleted += result.get("scans_deleted", 0)
                    total_results_deleted += result.get("results_deleted", 0)
                    total_mentions_deleted += result.get("mentions_deleted", 0)
                    
                    if result.get("capped"):
                        orgs_capped += 1
                        
            except Exception as e:
                orgs_with_errors += 1
                logger.error(f"Error sweeping retention for org {org.id} ({org.name}): {e}", exc_info=True)
                results.append({
                    "org_id": org.id,
                    "org_name": org.name,
                    "error": str(e),
                })
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Summary logging
        logger.info("=" * 80)
        logger.info(f"Retention sweeper completed in {duration:.2f}s")
        logger.info(f"Organizations processed: {len(results)} / {len(orgs)}")
        logger.info(f"Organizations skipped (unlimited retention): {orgs_skipped}")
        logger.info(f"Organizations capped (more items remain): {orgs_capped}")
        logger.info(f"Organizations with errors: {orgs_with_errors}")
        logger.info(f"Total scans deleted: {total_scans_deleted}")
        logger.info(f"Total results deleted: {total_results_deleted}")
        logger.info(f"Total mentions deleted: {total_mentions_deleted}")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "duration_seconds": duration,
            "orgs_total": len(orgs),
            "orgs_processed": len(results),
            "orgs_skipped": orgs_skipped,
            "orgs_capped": orgs_capped,
            "orgs_with_errors": orgs_with_errors,
            "total_scans_deleted": total_scans_deleted,
            "total_results_deleted": total_results_deleted,
            "total_mentions_deleted": total_mentions_deleted,
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"Retention sweeper job failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db.close()


if __name__ == "__main__":
    # Allow running this job directly for testing
    logging.basicConfig(level=logging.INFO)
    result = run_retention_sweeper()
    print(result)

