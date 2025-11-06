"""Analytics schemas."""
from typing import List, Optional

from pydantic import BaseModel


class RecentScanResponse(BaseModel):
    """Recent scan summary."""

    id: int
    name: str
    models_tested: int
    mentions_found: int
    time_ago: str


class UsageMetric(BaseModel):
    """Usage metric for a single resource."""

    used: int
    limit: Optional[int]  # None means unlimited
    warn: bool  # True if >= 80% of limit


class UsageResponse(BaseModel):
    """Usage summary response."""

    scans: UsageMetric
    prompts: UsageMetric
    ai_pages: UsageMetric
    period_start: str  # ISO format datetime of billing period start
    period_end: str  # ISO format datetime of billing period end


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response."""

    visibility_score: float
    visibility_growth: float
    visibility_score_version: str  # Version of the score calculation formula
    total_mentions: int
    mention_growth: float
    active_pages: int
    pages_published_this_month: int
    scan_runs: int
    recent_scans: List[RecentScanResponse]
    usage: Optional[UsageResponse] = None  # Usage metrics with warnings

