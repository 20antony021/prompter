"""Page generation job."""
import asyncio
import logging
import os
import sys

# Add parent directory to path to import from api
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../api"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.brand import Brand
from app.models.knowledge_page import KnowledgePage
from app.services.page_generator import PageGenerator

logger = logging.getLogger(__name__)

# Create database session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


async def generate_page_content_async(
    page_id: int, urls_to_crawl: list[str] = None
) -> None:
    """
    Generate page content asynchronously.

    Args:
        page_id: ID of knowledge page to generate
        urls_to_crawl: Optional list of URLs to crawl
    """
    db = SessionLocal()

    try:
        # Get page
        page = db.query(KnowledgePage).filter(KnowledgePage.id == page_id).first()

        if not page:
            logger.error(f"Page {page_id} not found")
            return

        logger.info(f"Generating content for page {page_id}: {page.title}")

        # Get brand
        brand = db.query(Brand).filter(Brand.id == page.brand_id).first()

        # Generate page
        generator = PageGenerator(brand)
        page_data = await generator.generate_page(
            title=page.title,
            urls_to_crawl=urls_to_crawl,
            vertical="saas",  # TODO: Get from brand
        )

        # Update page
        page.mdx = page_data["mdx"]
        page.html = page_data["html"]
        page.schema_json = page_data["schema_json"]
        page.score = page_data["score"]

        db.commit()

        logger.info(f"Page {page_id} generated successfully with score {page.score}")

    except Exception as e:
        logger.error(f"Error generating page {page_id}: {e}")

    finally:
        db.close()


def generate_page_content(page_id: int, urls_to_crawl: list[str] = None) -> None:
    """
    Synchronous wrapper for async page generation.

    Args:
        page_id: ID of knowledge page to generate
        urls_to_crawl: Optional list of URLs to crawl
    """
    asyncio.run(generate_page_content_async(page_id, urls_to_crawl))

