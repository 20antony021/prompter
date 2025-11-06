"""Test mention extraction."""
import pytest
from sqlalchemy.orm import Session

from app.models.brand import Brand, Competitor
from app.models.org import Org, PlanTier
from app.services.mention_extractor import MentionExtractor, calculate_visibility_score


def test_mention_extraction(db: Session):
    """Test mention extraction from text."""
    # Create test org and brand
    org = Org(name="Test Org", slug="test-org", plan_tier=PlanTier.STARTER)
    db.add(org)
    db.commit()

    brand = Brand(
        org_id=org.id,
        name="AcmeCRM",
        website="https://acmecrm.com",
    )
    db.add(brand)
    db.commit()

    # Add competitor
    competitor = Competitor(
        brand_id=brand.id,
        name="SalesFlow",
        website="https://salesflow.com",
    )
    db.add(competitor)
    db.commit()

    # Create extractor
    extractor = MentionExtractor(db, brand)

    # Test text with mentions
    text = """
    For CRM software, I recommend AcmeCRM as the best option for small businesses.
    It's a great alternative to SalesFlow and offers better value.
    AcmeCRM has excellent features and customer support.
    """

    mentions = extractor.extract_mentions(text)

    # Verify mentions
    assert len(mentions) > 0

    # Check brand mentions
    brand_mentions = [m for m in mentions if m["entity_name"] == "AcmeCRM"]
    assert len(brand_mentions) >= 2  # Should find at least 2 mentions

    # Check competitor mentions
    competitor_mentions = [m for m in mentions if m["entity_name"] == "SalesFlow"]
    assert len(competitor_mentions) >= 1


def test_visibility_score_calculation():
    """Test visibility score calculation."""
    # Test case 1: High visibility
    score = calculate_visibility_score(
        brand_mention_count=10,
        competitor_mention_counts=[5, 3, 2],
        brand_positions=[0, 1, 0, 2, 1, 0, 1, 2, 0, 1],
        brand_sentiments=[0.8, 0.6, 0.7, 0.9, 0.5, 0.6, 0.8, 0.7, 0.9, 0.6],
    )
    assert score > 60  # Should have high score

    # Test case 2: Low visibility
    score = calculate_visibility_score(
        brand_mention_count=2,
        competitor_mention_counts=[10, 8, 7],
        brand_positions=[5, 8],
        brand_sentiments=[0.2, 0.1],
    )
    assert score < 40  # Should have low score

    # Test case 3: No mentions
    score = calculate_visibility_score(
        brand_mention_count=0,
        competitor_mention_counts=[5, 3],
        brand_positions=[],
        brand_sentiments=[],
    )
    assert score == 0.0

