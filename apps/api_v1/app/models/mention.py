"""Mention model - extracted brand mentions from scan results."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.scan import ScanResult


class EntityType(str, Enum):
    """Entity type for mentions."""

    BRAND = "brand"
    COMPETITOR = "competitor"
    OTHER = "other"


class Mention(Base):
    """Mention model - extracted brand/competitor reference."""

    __tablename__ = "mentions"

    id = Column(Integer, primary_key=True, index=True)
    scan_result_id = Column(
        Integer, ForeignKey("scan_results.id", ondelete="CASCADE"), nullable=False
    )
    entity_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(SQLEnum(EntityType), nullable=False, default=EntityType.OTHER, index=True)
    sentiment = Column(Float, nullable=True)  # -1.0 to 1.0
    position_index = Column(Integer, nullable=True)  # Position in response (0-based)
    confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    cited_urls_json = Column(JSON, nullable=True)  # List of URLs cited with this mention
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    scan_result: "ScanResult" = relationship("ScanResult", back_populates="mentions")

    def __repr__(self) -> str:
        return f"<Mention(id={self.id}, entity={self.entity_name}, type={self.entity_type})>"


# Import for SQLEnum
from sqlalchemy import Enum as SQLEnum

