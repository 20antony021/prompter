"""
Impact Analyzer Service

Analyzes the impact of published knowledge pages on brand visibility.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_page import KnowledgePage
from app.models.mention import Mention
from app.models.scan import ScanResult, ScanRun


class ImpactAnalyzer:
    """Analyzes before/after impact of knowledge page publication."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def get_page_impact(
        self,
        page_id: str,
        before_days: int = 30,
        after_days: int = 30
    ) -> Dict:
        """
        Analyze the impact of a published knowledge page.
        
        Args:
            page_id: Knowledge page ID
            before_days: Days before publication to analyze
            after_days: Days after publication to analyze
            
        Returns:
            Dictionary with impact analysis:
            {
                "page": {
                    "id": "...",
                    "title": "...",
                    "published_at": "...",
                    "status": "published"
                },
                "before": {
                    "period": {"start": "...", "end": "..."},
                    "mentions": 50,
                    "avg_sentiment": 0.6,
                    "avg_position": 3.2,
                    "visibility_score": 45.5
                },
                "after": {
                    "period": {"start": "...", "end": "..."},
                    "mentions": 75,
                    "avg_sentiment": 0.8,
                    "avg_position": 1.8,
                    "visibility_score": 68.3
                },
                "changes": {
                    "mentions_delta": 25,
                    "mentions_change_pct": 50.0,
                    "sentiment_delta": 0.2,
                    "sentiment_change_pct": 33.3,
                    "position_delta": -1.4,
                    "position_change_pct": -43.8,
                    "visibility_score_delta": 22.8,
                    "visibility_score_change_pct": 50.1
                },
                "statistical_significance": {
                    "is_significant": true,
                    "confidence_level": 0.95,
                    "sample_size_sufficient": true
                },
                "insights": [
                    "Significant improvement in visibility score (+50.1%)",
                    "Better positioning in AI responses (avg position improved from 3.2 to 1.8)",
                    ...
                ]
            }
        """
        # Get page details
        page = await self._get_page(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        if page.status != 'published' or not page.published_at:
            return {
                "page": {
                    "id": page.id,
                    "title": page.title,
                    "status": page.status,
                    "published_at": None
                },
                "error": "Page is not published. Impact analysis requires a published page with a publication date."
            }
        
        # Define periods
        published_at = page.published_at
        before_start = published_at - timedelta(days=before_days)
        before_end = published_at
        after_start = published_at
        after_end = published_at + timedelta(days=after_days)
        
        # Don't analyze future dates
        now = datetime.utcnow()
        if after_end > now:
            after_end = now
            actual_after_days = (after_end - after_start).days
        else:
            actual_after_days = after_days
        
        # Get metrics for before period
        before_metrics = await self._get_period_metrics(
            brand_id=page.brand_id,
            start_date=before_start,
            end_date=before_end
        )
        
        # Get metrics for after period
        after_metrics = await self._get_period_metrics(
            brand_id=page.brand_id,
            start_date=after_start,
            end_date=after_end
        )
        
        # Calculate changes
        changes = self._calculate_changes(before_metrics, after_metrics)
        
        # Assess statistical significance
        significance = self._assess_statistical_significance(
            before_metrics,
            after_metrics,
            before_days,
            actual_after_days
        )
        
        # Generate insights
        insights = self._generate_insights(
            before_metrics,
            after_metrics,
            changes,
            significance
        )
        
        return {
            "page": {
                "id": page.id,
                "title": page.title,
                "published_at": published_at.isoformat(),
                "status": page.status,
                "subdomain": page.subdomain,
                "path": page.path
            },
            "before": {
                "period": {
                    "start": before_start.isoformat(),
                    "end": before_end.isoformat(),
                    "days": before_days
                },
                **before_metrics
            },
            "after": {
                "period": {
                    "start": after_start.isoformat(),
                    "end": after_end.isoformat(),
                    "days": actual_after_days
                },
                **after_metrics
            },
            "changes": changes,
            "statistical_significance": significance,
            "insights": insights
        }
    
    async def _get_page(self, page_id: str) -> Optional[KnowledgePage]:
        """Get page by ID."""
        query = select(KnowledgePage).where(KnowledgePage.id == page_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_period_metrics(
        self,
        brand_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get aggregated metrics for a time period."""
        # Query mentions for brand
        query = (
            select(
                func.count(Mention.id).label('mention_count'),
                func.avg(Mention.sentiment).label('avg_sentiment'),
                func.avg(Mention.position_index).label('avg_position'),
                func.avg(Mention.confidence).label('avg_confidence')
            )
            .join(ScanResult, Mention.scan_result_id == ScanResult.id)
            .join(ScanRun, ScanResult.scan_run_id == ScanRun.id)
            .where(
                and_(
                    ScanRun.brand_id == brand_id,
                    Mention.entity_type == 'brand',
                    ScanRun.created_at >= start_date,
                    ScanRun.created_at <= end_date,
                    ScanRun.status == 'done'
                )
            )
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row or row.mention_count == 0:
            return {
                "mentions": 0,
                "avg_sentiment": 0.0,
                "avg_position": 0.0,
                "avg_confidence": 0.0,
                "visibility_score": 0.0
            }
        
        # Calculate visibility score (simplified version)
        # In production, use the full visibility score calculator
        visibility_score = self._calculate_simple_visibility_score(
            mentions=row.mention_count,
            avg_position=float(row.avg_position) if row.avg_position else 0.0,
            avg_sentiment=float(row.avg_sentiment) if row.avg_sentiment else 0.0
        )
        
        return {
            "mentions": row.mention_count,
            "avg_sentiment": round(float(row.avg_sentiment) if row.avg_sentiment else 0.0, 3),
            "avg_position": round(float(row.avg_position) if row.avg_position else 0.0, 2),
            "avg_confidence": round(float(row.avg_confidence) if row.avg_confidence else 0.0, 3),
            "visibility_score": round(visibility_score, 2)
        }
    
    def _calculate_simple_visibility_score(
        self,
        mentions: int,
        avg_position: float,
        avg_sentiment: float
    ) -> float:
        """Calculate a simplified visibility score for impact analysis."""
        if mentions == 0:
            return 0.0
        
        # Normalize mentions (assume max 100 for scaling)
        mention_score = min(mentions / 100.0, 1.0) * 40
        
        # Position score (lower is better, scale 0-10 range to 0-30)
        position_score = max(0, 30 - (avg_position * 3)) if avg_position > 0 else 0
        
        # Sentiment score (-1 to 1 range to 0-30)
        sentiment_score = ((avg_sentiment + 1) / 2) * 30
        
        return mention_score + position_score + sentiment_score
    
    def _calculate_changes(
        self,
        before: Dict,
        after: Dict
    ) -> Dict:
        """Calculate changes between before and after periods."""
        changes = {}
        
        for metric in ["mentions", "avg_sentiment", "avg_position", "avg_confidence", "visibility_score"]:
            before_val = before.get(metric, 0)
            after_val = after.get(metric, 0)
            
            delta = after_val - before_val
            
            # Calculate percentage change
            if before_val != 0:
                change_pct = (delta / before_val) * 100
            elif after_val != 0:
                change_pct = 100.0  # From zero to something
            else:
                change_pct = 0.0
            
            changes[f"{metric}_delta"] = round(delta, 3)
            changes[f"{metric}_change_pct"] = round(change_pct, 2)
        
        return changes
    
    def _assess_statistical_significance(
        self,
        before: Dict,
        after: Dict,
        before_days: int,
        after_days: int
    ) -> Dict:
        """
        Assess statistical significance of changes.
        
        This is a simplified version. In production, use proper statistical tests
        (e.g., t-test, Mann-Whitney U test).
        """
        # Check sample size
        min_mentions = 30  # Minimum for reasonable confidence
        sample_size_sufficient = (
            before["mentions"] >= min_mentions and 
            after["mentions"] >= min_mentions
        )
        
        # Simple significance check based on magnitude of change
        visibility_change_pct = abs(
            after["visibility_score"] - before["visibility_score"]
        ) / max(before["visibility_score"], 1) * 100
        
        # Consider significant if change > 20% and sample size sufficient
        is_significant = visibility_change_pct > 20 and sample_size_sufficient
        
        # Confidence level (simplified)
        if is_significant and sample_size_sufficient:
            confidence_level = 0.95
        elif sample_size_sufficient:
            confidence_level = 0.80
        else:
            confidence_level = 0.50
        
        return {
            "is_significant": is_significant,
            "confidence_level": confidence_level,
            "sample_size_sufficient": sample_size_sufficient,
            "note": "Simplified significance test. Use proper statistical methods in production."
        }
    
    def _generate_insights(
        self,
        before: Dict,
        after: Dict,
        changes: Dict,
        significance: Dict
    ) -> list[str]:
        """Generate actionable insights from impact analysis."""
        insights = []
        
        # Visibility score insights
        vis_change = changes["visibility_score_change_pct"]
        if vis_change > 20:
            insights.append(f"Significant improvement in visibility score (+{vis_change:.1f}%)")
        elif vis_change < -20:
            insights.append(f"Visibility score declined ({vis_change:.1f}%). Review page content and optimization.")
        else:
            insights.append(f"Modest change in visibility score ({vis_change:+.1f}%)")
        
        # Mentions insights
        mentions_change = changes["mentions_change_pct"]
        if mentions_change > 30:
            insights.append(f"Strong increase in mentions (+{mentions_change:.1f}%)")
        elif mentions_change < -30:
            insights.append(f"Decrease in mentions ({mentions_change:.1f}%). May need content refresh.")
        
        # Position insights
        pos_before = before["avg_position"]
        pos_after = after["avg_position"]
        if pos_before > 0 and pos_after > 0:
            if pos_after < pos_before:
                improvement = pos_before - pos_after
                insights.append(f"Better positioning in AI responses (avg position improved by {improvement:.1f})")
            elif pos_after > pos_before:
                decline = pos_after - pos_before
                insights.append(f"Lower positioning in AI responses (avg position declined by {decline:.1f})")
        
        # Sentiment insights
        sent_change = changes["avg_sentiment_change_pct"]
        if sent_change > 15:
            insights.append(f"Improved sentiment (+{sent_change:.1f}%)")
        elif sent_change < -15:
            insights.append(f"Sentiment declined ({sent_change:.1f}%). Review messaging.")
        
        # Statistical significance
        if not significance["is_significant"]:
            if not significance["sample_size_sufficient"]:
                insights.append("Limited data available. Results may not be statistically significant.")
            else:
                insights.append("Changes are not statistically significant. Continue monitoring.")
        
        # ROI insight
        if vis_change > 30:
            insights.append("Strong ROI from page publication. Consider creating similar content.")
        
        return insights

