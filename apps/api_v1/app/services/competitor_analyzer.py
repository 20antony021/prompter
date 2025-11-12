"""
Competitor Analyzer Service

Analyzes competitive landscape and market share.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mention import Mention
from app.models.scan import ScanResult, ScanRun
from app.models.brand import Brand, Competitor


class CompetitorAnalyzer:
    """Analyzes competitive positioning and market share."""
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def get_competitor_analysis(
        self,
        brand_id: str,
        days: int = 30
    ) -> Dict:
        """
        Get comprehensive competitor analysis.
        
        Args:
            brand_id: Brand ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with competitor analysis:
            {
                "brand": {
                    "name": "...",
                    "mentions": 100,
                    "avg_sentiment": 0.8,
                    "avg_position": 1.5,
                    "market_share_pct": 45.5
                },
                "competitors": [
                    {
                        "name": "...",
                        "mentions": 80,
                        "avg_sentiment": 0.6,
                        "avg_position": 2.3,
                        "market_share_pct": 36.4
                    },
                    ...
                ],
                "rankings": {
                    "by_mentions": [...],
                    "by_sentiment": [...],
                    "by_position": [...]
                },
                "period": {"start": "...", "end": "...", "days": 30},
                "total_mentions": 220
            }
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get brand info
        brand = await self._get_brand(brand_id)
        if not brand:
            raise ValueError(f"Brand {brand_id} not found")
        
        # Get brand metrics
        brand_metrics = await self._get_entity_metrics(
            brand_id=brand_id,
            entity_type="brand",
            entity_name=brand.name,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get competitor metrics
        competitors_data = await self._get_all_competitors_metrics(
            brand_id=brand_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate total mentions
        total_mentions = brand_metrics["mentions"] + sum(
            c["mentions"] for c in competitors_data
        )
        
        # Calculate market share
        if total_mentions > 0:
            brand_metrics["market_share_pct"] = round(
                (brand_metrics["mentions"] / total_mentions) * 100, 2
            )
            for comp in competitors_data:
                comp["market_share_pct"] = round(
                    (comp["mentions"] / total_mentions) * 100, 2
                )
        else:
            brand_metrics["market_share_pct"] = 0.0
            for comp in competitors_data:
                comp["market_share_pct"] = 0.0
        
        # Create rankings
        all_entities = [brand_metrics] + competitors_data
        
        rankings = {
            "by_mentions": sorted(
                [{"name": e["name"], "value": e["mentions"]} for e in all_entities],
                key=lambda x: x["value"],
                reverse=True
            ),
            "by_sentiment": sorted(
                [{"name": e["name"], "value": e["avg_sentiment"]} for e in all_entities],
                key=lambda x: x["value"],
                reverse=True
            ),
            "by_position": sorted(
                [{"name": e["name"], "value": e["avg_position"]} for e in all_entities],
                key=lambda x: x["value"]  # Lower position is better
            )
        }
        
        return {
            "brand": brand_metrics,
            "competitors": competitors_data,
            "rankings": rankings,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "total_mentions": total_mentions
        }
    
    async def _get_brand(self, brand_id: str) -> Optional[Brand]:
        """Get brand by ID."""
        query = select(Brand).where(Brand.id == brand_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_entity_metrics(
        self,
        brand_id: str,
        entity_type: str,
        entity_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get metrics for a specific entity."""
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
                    Mention.entity_type == entity_type,
                    Mention.entity_name == entity_name,
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
                "name": entity_name,
                "mentions": 0,
                "avg_sentiment": 0.0,
                "avg_position": 0.0,
                "avg_confidence": 0.0
            }
        
        return {
            "name": entity_name,
            "mentions": row.mention_count,
            "avg_sentiment": round(float(row.avg_sentiment) if row.avg_sentiment else 0.0, 3),
            "avg_position": round(float(row.avg_position) if row.avg_position else 0.0, 2),
            "avg_confidence": round(float(row.avg_confidence) if row.avg_confidence else 0.0, 3)
        }
    
    async def _get_all_competitors_metrics(
        self,
        brand_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get metrics for all competitors."""
        # Get list of competitors
        query = select(Competitor).where(Competitor.brand_id == brand_id)
        result = await self.db.execute(query)
        competitors = result.scalars().all()
        
        # Get metrics for each competitor
        competitors_data = []
        for competitor in competitors:
            metrics = await self._get_entity_metrics(
                brand_id=brand_id,
                entity_type="competitor",
                entity_name=competitor.name,
                start_date=start_date,
                end_date=end_date
            )
            competitors_data.append(metrics)
        
        # Sort by mentions (descending)
        competitors_data.sort(key=lambda x: x["mentions"], reverse=True)
        
        return competitors_data
    
    async def get_competitive_positioning(
        self,
        brand_id: str,
        days: int = 30
    ) -> Dict:
        """
        Get competitive positioning matrix.
        
        Returns positioning based on mentions vs sentiment quadrants.
        """
        analysis = await self.get_competitor_analysis(brand_id, days)
        
        # Calculate averages for positioning
        all_entities = [analysis["brand"]] + analysis["competitors"]
        
        if not all_entities:
            return {
                "quadrants": {},
                "brand_position": "unknown",
                "insights": []
            }
        
        avg_mentions = sum(e["mentions"] for e in all_entities) / len(all_entities)
        avg_sentiment = sum(e["avg_sentiment"] for e in all_entities) / len(all_entities)
        
        # Classify entities into quadrants
        quadrants = {
            "leaders": [],  # High mentions, high sentiment
            "challengers": [],  # High mentions, low sentiment
            "niche_positive": [],  # Low mentions, high sentiment
            "emerging": []  # Low mentions, low sentiment
        }
        
        for entity in all_entities:
            high_mentions = entity["mentions"] >= avg_mentions
            high_sentiment = entity["avg_sentiment"] >= avg_sentiment
            
            if high_mentions and high_sentiment:
                quadrants["leaders"].append(entity["name"])
            elif high_mentions and not high_sentiment:
                quadrants["challengers"].append(entity["name"])
            elif not high_mentions and high_sentiment:
                quadrants["niche_positive"].append(entity["name"])
            else:
                quadrants["emerging"].append(entity["name"])
        
        # Determine brand position
        brand_name = analysis["brand"]["name"]
        brand_position = "unknown"
        for quadrant, entities in quadrants.items():
            if brand_name in entities:
                brand_position = quadrant
                break
        
        # Generate insights
        insights = self._generate_positioning_insights(
            analysis["brand"],
            analysis["competitors"],
            brand_position
        )
        
        return {
            "quadrants": quadrants,
            "brand_position": brand_position,
            "averages": {
                "mentions": round(avg_mentions, 2),
                "sentiment": round(avg_sentiment, 3)
            },
            "insights": insights
        }
    
    def _generate_positioning_insights(
        self,
        brand: Dict,
        competitors: List[Dict],
        position: str
    ) -> List[str]:
        """Generate actionable insights from positioning data."""
        insights = []
        
        # Position-specific insights
        if position == "leaders":
            insights.append("Your brand is well-positioned as a market leader with strong visibility and positive sentiment.")
        elif position == "challengers":
            insights.append("Your brand has high visibility but sentiment could be improved. Focus on improving brand perception.")
        elif position == "niche_positive":
            insights.append("Your brand has positive sentiment but limited visibility. Focus on increasing mention frequency.")
        elif position == "emerging":
            insights.append("Opportunity to improve both visibility and sentiment. Consider content optimization and brand positioning.")
        
        # Competitive insights
        if competitors:
            top_competitor = max(competitors, key=lambda x: x["mentions"])
            if top_competitor["mentions"] > brand["mentions"]:
                gap = top_competitor["mentions"] - brand["mentions"]
                insights.append(f"Top competitor '{top_competitor['name']}' has {gap} more mentions. Consider increasing content presence.")
            
            best_sentiment = max(competitors, key=lambda x: x["avg_sentiment"])
            if best_sentiment["avg_sentiment"] > brand["avg_sentiment"]:
                insights.append(f"'{best_sentiment['name']}' has better sentiment. Analyze their messaging and positioning.")
        
        # Market share insights
        if brand.get("market_share_pct", 0) < 25:
            insights.append("Market share below 25%. Focus on increasing AI visibility through optimized content.")
        elif brand.get("market_share_pct", 0) > 50:
            insights.append("Strong market dominance with >50% share. Maintain and defend your position.")
        
        return insights

