"""Mention extraction service - extract brand mentions from LLM responses."""
import logging
import re
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.brand import Brand, Competitor
from app.models.mention import EntityType

logger = logging.getLogger(__name__)

# Visibility Score Formula Version
# Update this when changing the calculation logic to maintain historical accuracy
VISIBILITY_SCORE_VERSION = "1.0.0"


class MentionExtractor:
    """Extract brand and competitor mentions from text."""

    def __init__(self, db: Session, brand: Brand):
        """
        Initialize mention extractor.

        Args:
            db: Database session
            brand: Brand to extract mentions for
        """
        self.db = db
        self.brand = brand

        # Build entity map
        self.entity_map: Dict[str, Tuple[str, EntityType]] = {}
        self._build_entity_map()

    def _build_entity_map(self) -> None:
        """Build map of entity names to their types."""
        # Add brand
        brand_name_lower = self.brand.name.lower()
        self.entity_map[brand_name_lower] = (self.brand.name, EntityType.BRAND)

        # Add brand aliases (simple variations)
        brand_words = self.brand.name.split()
        if len(brand_words) > 1:
            # Add variations without common suffixes
            for suffix in ["Inc", "Inc.", "LLC", "Ltd", "Corporation", "Corp"]:
                name_without_suffix = self.brand.name.replace(suffix, "").strip()
                if name_without_suffix:
                    self.entity_map[name_without_suffix.lower()] = (
                        self.brand.name,
                        EntityType.BRAND,
                    )

        # Add competitors
        competitors = (
            self.db.query(Competitor).filter(Competitor.brand_id == self.brand.id).all()
        )

        for competitor in competitors:
            comp_name_lower = competitor.name.lower()
            self.entity_map[comp_name_lower] = (competitor.name, EntityType.COMPETITOR)

            # Add competitor aliases
            comp_words = competitor.name.split()
            if len(comp_words) > 1:
                for suffix in ["Inc", "Inc.", "LLC", "Ltd", "Corporation", "Corp"]:
                    name_without_suffix = competitor.name.replace(suffix, "").strip()
                    if name_without_suffix:
                        self.entity_map[name_without_suffix.lower()] = (
                            competitor.name,
                            EntityType.COMPETITOR,
                        )

    def extract_mentions(
        self, text: str
    ) -> List[Dict[str, any]]:
        """
        Extract mentions from text.

        Args:
            text: Text to extract mentions from

        Returns:
            List of mention dictionaries
        """
        mentions = []
        text_lower = text.lower()

        # Find all entity mentions
        for entity_key, (entity_name, entity_type) in self.entity_map.items():
            # Find all occurrences
            pattern = r'\b' + re.escape(entity_key) + r'\b'
            matches = list(re.finditer(pattern, text_lower))

            for match in matches:
                # Calculate position index (which mention number is this?)
                position_index = len([m for m in mentions if m["entity_name"] == entity_name])

                # Extract context around mention for sentiment analysis
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                # Simple sentiment analysis based on keywords
                sentiment = self._analyze_sentiment(context)

                # Extract any URLs from context
                urls = self._extract_urls(context)

                mention = {
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "position_index": position_index,
                    "sentiment": sentiment,
                    "confidence": 0.8,  # High confidence for exact matches
                    "cited_urls": urls,
                }

                mentions.append(mention)

        # Also check for fuzzy matches (simple Levenshtein-like approach)
        # For production, consider using more sophisticated NER or embeddings

        return mentions

    def _analyze_sentiment(self, context: str) -> float:
        """
        Analyze sentiment of context.

        Args:
            context: Text context

        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        context_lower = context.lower()

        positive_words = [
            "best",
            "excellent",
            "great",
            "recommend",
            "top",
            "leading",
            "superior",
            "innovative",
            "powerful",
            "reliable",
            "trusted",
            "popular",
        ]

        negative_words = [
            "worst",
            "poor",
            "bad",
            "avoid",
            "inferior",
            "lacking",
            "disappointing",
            "unreliable",
            "buggy",
            "expensive",
        ]

        positive_count = sum(1 for word in positive_words if word in context_lower)
        negative_count = sum(1 for word in negative_words if word in context_lower)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        # Normalize to -1.0 to 1.0
        sentiment = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, sentiment))

    def _extract_urls(self, text: str) -> List[str]:
        """
        Extract URLs from text.

        Args:
            text: Text to extract URLs from

        Returns:
            List of URLs
        """
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls[:5]  # Limit to 5 URLs


def calculate_visibility_score(
    brand_mention_count: int,
    competitor_mention_counts: List[int],
    brand_positions: List[int],
    brand_sentiments: List[float],
) -> float:
    """
    Calculate visibility score for a brand.
    
    Formula Version: 1.0.0
    Components:
    - Base Score (40 pts): Ratio of brand mentions to total mentions
    - Position Score (30 pts): Earlier position in responses = higher score
    - Sentiment Score (30 pts): Average sentiment of brand mentions
    
    Total: 0-100 points

    Args:
        brand_mention_count: Number of brand mentions
        competitor_mention_counts: List of mention counts for each competitor
        brand_positions: List of position indices for brand mentions
        brand_sentiments: List of sentiment scores for brand mentions

    Returns:
        Visibility score (0-100)
    """
    # Base score from mention count (up to 40 points)
    total_mentions = brand_mention_count + sum(competitor_mention_counts)
    if total_mentions == 0:
        return 0.0

    mention_ratio = brand_mention_count / total_mentions
    base_score = mention_ratio * 40  # Up to 40 points

    # Position score (earlier mentions score higher, up to 30 points)
    position_score = 0.0
    if brand_positions:
        # Positions: 0 = first, higher = later
        # Score: earlier positions get more points
        avg_position = sum(brand_positions) / len(brand_positions)
        # Convert to score (max 30 points if always first)
        position_score = max(0, 30 - (avg_position * 2))

    # Sentiment score (positive sentiment adds points, up to 30 points)
    sentiment_score = 0.0
    if brand_sentiments:
        avg_sentiment = sum(brand_sentiments) / len(brand_sentiments)
        # Sentiment is -1 to 1, normalize to 0-30
        sentiment_score = (avg_sentiment + 1) * 15  # 0 to 30 points

    # Total score
    total_score = base_score + position_score + sentiment_score

    return min(100.0, max(0.0, total_score))

