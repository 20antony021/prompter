"""Knowledge page model - AI-optimized content pages."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.brand import Brand


class PageStatus(str, Enum):
    """Knowledge page status."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class KnowledgePage(Base):
    """Knowledge page model - SEO and AI-optimized content."""

    __tablename__ = "knowledge_pages"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    status = Column(SQLEnum(PageStatus), nullable=False, default=PageStatus.DRAFT, index=True)
    html = Column(Text, nullable=True)  # Rendered HTML
    mdx = Column(Text, nullable=True)  # Source MDX
    schema_json = Column(JSON, nullable=True)  # JSON-LD structured data
    score = Column(Float, nullable=True)  # Page health score (0-100)
    published_at = Column(DateTime, nullable=True)
    canonical_url = Column(String(500), nullable=True)
    path = Column(String(500), nullable=True)  # URL path
    subdomain = Column(String(255), nullable=True, index=True)  # e.g., "acme"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand: "Brand" = relationship("Brand", back_populates="knowledge_pages")

    def __repr__(self) -> str:
        return f"<KnowledgePage(id={self.id}, title={self.title}, status={self.status})>"

