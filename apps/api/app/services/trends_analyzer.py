"""
Trends Analyzer Service

Analyzes mention trends over time for brands and competitors.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mention import Mention
from app.models.scan import ScanResult, ScanRun
from app.models.brand import Brand
from app.services.mention_extractor import calculate_visibility_score_with_breakdown, VISIBILITY_SCORE_VERSION


class TrendsAnalyzer:
    """Analyzes mention trends and patterns over time."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def get_mention_trends(
        self,
        brand_id: str,
        days: int = 30,
        granularity: str = "daily"
    ) -> Dict:
        """
        Get mention trends over time.
        
        Args:
            brand_id: Brand ID
            days: Number of days to analyze (7, 30, or 90)
            granularity: Time granularity ("daily" or "weekly")
            
        Returns:
            Dictionary with trend data:
            {
                "period": {"start": "...", "end": "..."},
                "granularity": "daily",
                "brand_trend": [{"date": "...", "mentions": 10, "sentiment": 0.8}, ...],
                "competitor_trends": {
                    "Competitor A": [{"date": "...", "mentions": 5, "sentiment": 0.6}, ...],
                    ...
                },
                "summary": {
                    "brand_total": 100,
                    "brand_avg_sentiment": 0.75,
                    "competitor_total": 80,
                    "competitor_avg_sentiment": 0.65,
                    "brand_growth_pct": 15.5
                }
            }
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get brand mentions trend
        brand_trend = await self._get_entity_trend(
            brand_id=brand_id,
            entity_type="brand",
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        
        # Get competitor mentions trends
        competitor_trends = await self._get_competitor_trends(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        
        # Calculate summary statistics
        summary = await self._calculate_trend_summary(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date,
            days=days
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "granularity": granularity,
            "brand_trend": brand_trend,
            "competitor_trends": competitor_trends,
            "summary": summary
        }
    
    async def _get_entity_trend(
        self,
        brand_id: str,
        entity_type: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str,
        entity_name: Optional[str] = None
    ) -> List[Dict]:
        """Get trend data for a specific entity (brand or competitor)."""
        # Build query
        query = (
            select(
                func.date_trunc(granularity.replace('ly', ''), ScanRun.created_at).label('period'),
                func.count(Mention.id).label('mention_count'),
                func.avg(Mention.sentiment).label('avg_sentiment')
            )
            .join(ScanResult, Mention.scan_result_id == ScanResult.id)
            .join(ScanRun, ScanResult.scan_run_id == ScanRun.id)
            .where(
                and_(
                    ScanRun.brand_id == brand_id,
                    Mention.entity_type == entity_type,
                    ScanRun.created_at >= start_date,
                    ScanRun.created_at <= end_date,
                    ScanRun.status == 'done'
                )
            )
            .group_by('period')
            .order_by('period')
        )
        
        if entity_name:
            query = query.where(Mention.entity_name == entity_name)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Format results
        trend = []
        for row in rows:
            trend.append({
                "date": row.period.isoformat(),
                "mentions": row.mention_count,
                "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else 0.0
            })
        
        return trend
    
    async def _get_competitor_trends(
        self,
        brand_id: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str
    ) -> Dict[str, List[Dict]]:
        """Get trends for all competitors."""
        # Get list of competitors for this brand
        from app.models.brand import Competitor
        
        query = select(Competitor).where(Competitor.brand_id == brand_id)
        result = await self.db.execute(query)
        competitors = result.scalars().all()
        
        # Get trend for each competitor
        trends = {}
        for competitor in competitors:
            competitor_trend = await self._get_entity_trend(
                brand_id=brand_id,
                entity_type="competitor",
                entity_name=competitor.name,
                start_date=start_date,
                end_date=end_date,
                granularity=granularity
            )
            trends[competitor.name] = competitor_trend
        
        return trends
    
    async def _calculate_trend_summary(
        self,
        brand_id: str,
        start_date: datetime,
        end_date: datetime,
        days: int
    ) -> Dict:
        """Calculate summary statistics for the period."""
        # Current period stats
        current_query = (
            select(
                Mention.entity_type,
                func.count(Mention.id).label('mention_count'),
                func.avg(Mention.sentiment).label('avg_sentiment')
            )
            .join(ScanResult, Mention.scan_result_id == ScanResult.id)
            .join(ScanRun, ScanResult.scan_run_id == ScanRun.id)
            .where(
                and_(
                    ScanRun.brand_id == brand_id,
                    ScanRun.created_at >= start_date,
                    ScanRun.created_at <= end_date,
                    ScanRun.status == 'done'
                )
            )
            .group_by(Mention.entity_type)
        )
        
        result = await self.db.execute(current_query)
        current_stats = {row.entity_type: row for row in result.all()}
        
        # Previous period stats (for growth calculation)
        prev_start = start_date - timedelta(days=days)
        prev_end = start_date
        
        prev_query = (
            select(
                Mention.entity_type,
                func.count(Mention.id).label('mention_count')
            )
            .join(ScanResult, Mention.scan_result_id == ScanResult.id)
            .join(ScanRun, ScanResult.scan_run_id == ScanRun.id)
            .where(
                and_(
                    ScanRun.brand_id == brand_id,
                    ScanRun.created_at >= prev_start,
                    ScanRun.created_at < prev_end,
                    ScanRun.status == 'done'
                )
            )
            .group_by(Mention.entity_type)
        )
        
        result = await self.db.execute(prev_query)
        prev_stats = {row.entity_type: row for row in result.all()}
        
        # Calculate growth
        brand_current = current_stats.get('brand')
        brand_prev = prev_stats.get('brand')
        
        brand_growth_pct = 0.0
        if brand_current and brand_prev:
            if brand_prev.mention_count > 0:
                brand_growth_pct = (
                    (brand_current.mention_count - brand_prev.mention_count) / 
                    brand_prev.mention_count * 100
                )
        elif brand_current and brand_current.mention_count > 0:
            brand_growth_pct = 100.0  # New mentions from zero
        
        # Build summary
        summary = {
            "brand_total": brand_current.mention_count if brand_current else 0,
            "brand_avg_sentiment": float(brand_current.avg_sentiment) if brand_current and brand_current.avg_sentiment else 0.0,
            "competitor_total": 0,
            "competitor_avg_sentiment": 0.0,
            "brand_growth_pct": round(brand_growth_pct, 2)
        }
        
        # Add competitor stats
        competitor_current = current_stats.get('competitor')
        if competitor_current:
            summary["competitor_total"] = competitor_current.mention_count
            summary["competitor_avg_sentiment"] = float(competitor_current.avg_sentiment) if competitor_current.avg_sentiment else 0.0
        
        return summary
    
    async def get_top_mentioned_entities(
        self,
        brand_id: str,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top mentioned entities (brand + competitors).
        
        Returns:
            List of entities with mention counts and sentiment
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(
                Mention.entity_name,
                Mention.entity_type,
                func.count(Mention.id).label('mention_count'),
                func.avg(Mention.sentiment).label('avg_sentiment'),
                func.avg(Mention.position_index).label('avg_position')
            )
            .join(ScanResult, Mention.scan_result_id == ScanResult.id)
            .join(ScanRun, ScanResult.scan_run_id == ScanRun.id)
            .where(
                and_(
                    ScanRun.brand_id == brand_id,
                    ScanRun.created_at >= start_date,
                    ScanRun.status == 'done'
                )
            )
            .group_by(Mention.entity_name, Mention.entity_type)
            .order_by(func.count(Mention.id).desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        entities = []
        for row in rows:
            entities.append({
                "name": row.entity_name,
                "type": row.entity_type,
                "mention_count": row.mention_count,
                "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else 0.0,
                "avg_position": float(row.avg_position) if row.avg_position else 0.0
            })
        
        return entities
    
    async def get_visibility_trends(
        self,
        brand_id: str,
        days: int = 30,
        granularity: str = "daily"
    ) -> Dict:
        """
        Get visibility score trends with sub-score decomposition.
        
        Args:
            brand_id: Brand ID
            days: Number of days to analyze (7, 30, or 90)
            granularity: Time granularity ("daily" or "weekly")
            
        Returns:
            Dictionary with visibility trends including sub-scores:
            {
                "period": {...},
                "granularity": "daily",
                "score_version": "1.0.0",
                "brand_visibility": [
                    {
                        "date": "...",
                        "score": 68.5,
                        "sub_scores": {
                            "mentions_score": 32.0,
                            "position_score": 18.5,
                            "sentiment_score": 18.0
                        }
                    }
                ],
                "competitor_visibility": {...},
                "summary": {...}
            }
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get brand data for each time period
        brand_trend = await self._get_visibility_trend_with_subscores(
            brand_id=brand_id,
            entity_type="brand",
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        
        # Get competitor trends
        competitor_trends = await self._get_competitor_visibility_trends(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        
        # Calculate summary statistics
        summary = await self._calculate_visibility_summary(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "granularity": granularity,
            "score_version": VISIBILITY_SCORE_VERSION,
            "brand_visibility": brand_trend,
            "competitor_visibility": competitor_trends,
            "summary": summary
        }
    
    async def _get_visibility_trend_with_subscores(
        self,
        brand_id: str,
        entity_type: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str,
        entity_name: Optional[str] = None
    ) -> List[Dict]:
        """Get visibility trend with sub-score decomposition for an entity."""
        # Build query to get mentions with position and sentiment per period
        query = (
            select(
                func.date_trunc(granularity.replace('ly', ''), ScanRun.created_at).label('period'),
                func.count(Mention.id).label('mention_count'),
                func.avg(Mention.sentiment).label('avg_sentiment'),
                func.avg(Mention.position_index).label('avg_position')
            )
            .join(ScanResult, Mention.scan_result_id == ScanResult.id)
            .join(ScanRun, ScanResult.scan_run_id == ScanRun.id)
            .where(
                and_(
                    ScanRun.brand_id == brand_id,
                    Mention.entity_type == entity_type,
                    ScanRun.created_at >= start_date,
                    ScanRun.created_at <= end_date,
                    ScanRun.status == 'done'
                )
            )
            .group_by('period')
            .order_by('period')
        )
        
        if entity_name:
            query = query.where(Mention.entity_name == entity_name)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # For each period, calculate visibility score with sub-scores
        trend = []
        for row in rows:
            # Get competitor counts for this period (simplified - assumes similar across periods)
            # In production, query competitor counts for each period
            competitor_counts = [5, 3, 2]  # Placeholder - should query actual data
            
            # Calculate visibility score with breakdown
            scores = calculate_visibility_score_with_breakdown(
                brand_mention_count=row.mention_count,
                competitor_mention_counts=competitor_counts,
                brand_positions=[row.avg_position] if row.avg_position else [],
                brand_sentiments=[row.avg_sentiment] if row.avg_sentiment else []
            )
            
            trend.append({
                "date": row.period.isoformat(),
                "score": scores["score"],
                "sub_scores": {
                    "mentions_score": scores["mentions_score"],
                    "position_score": scores["position_score"],
                    "sentiment_score": scores["sentiment_score"]
                }
            })
        
        return trend
    
    async def _get_competitor_visibility_trends(
        self,
        brand_id: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str
    ) -> Dict[str, List[Dict]]:
        """Get visibility trends for all competitors."""
        # Get list of competitors for this brand
        from app.models.brand import Competitor
        
        query = select(Competitor).where(Competitor.brand_id == brand_id)
        result = await self.db.execute(query)
        competitors = result.scalars().all()
        
        # Get trend for each competitor
        trends = {}
        for competitor in competitors:
            competitor_trend = await self._get_visibility_trend_with_subscores(
                brand_id=brand_id,
                entity_type="competitor",
                entity_name=competitor.name,
                start_date=start_date,
                end_date=end_date,
                granularity=granularity
            )
            trends[competitor.name] = competitor_trend
        
        return trends
    
    async def _calculate_visibility_summary(
        self,
        brand_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Calculate summary statistics for visibility trends."""
        # Get overall brand metrics for the period
        query = (
            select(
                func.count(Mention.id).label('mention_count'),
                func.avg(Mention.sentiment).label('avg_sentiment'),
                func.avg(Mention.position_index).label('avg_position')
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
                "overall_score": 0.0,
                "avg_mentions_score": 0.0,
                "avg_position_score": 0.0,
                "avg_sentiment_score": 0.0
            }
        
        # Calculate overall visibility score
        competitor_counts = [5, 3, 2]  # Placeholder - should query actual data
        scores = calculate_visibility_score_with_breakdown(
            brand_mention_count=row.mention_count,
            competitor_mention_counts=competitor_counts,
            brand_positions=[row.avg_position] if row.avg_position else [],
            brand_sentiments=[row.avg_sentiment] if row.avg_sentiment else []
        )
        
        return {
            "overall_score": scores["score"],
            "avg_mentions_score": scores["mentions_score"],
            "avg_position_score": scores["position_score"],
            "avg_sentiment_score": scores["sentiment_score"]
        }

