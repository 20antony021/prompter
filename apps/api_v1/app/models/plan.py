"""Plan and usage tracking models."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import BigInteger, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.org import Org


class Plan(Base):
    """Subscription plan model."""

    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    price_monthly = Column(Integer, nullable=False)  # In cents
    limits_json = Column(JSON, nullable=False)  # {"prompts_per_month": 100, "pages": 5, ...}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, code={self.code}, name={self.name})>"


class UsageMeter(Base):
    """Usage meter model - track monthly usage per org."""

    __tablename__ = "usage_meters"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    month = Column(String(7), nullable=False, index=True)  # YYYY-MM format
    prompts_used = Column(Integer, nullable=False, default=0)
    pages_hosted = Column(Integer, nullable=False, default=0)
    overage_cents = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    org: "Org" = relationship("Org", back_populates="usage_meters")

    def __repr__(self) -> str:
        return f"<UsageMeter(id={self.id}, org_id={self.org_id}, month={self.month})>"


class OrgMonthlyUsage(Base):
    """Monthly usage tracking with hard caps (no overages).
    
    Tracks usage per organization billing period (not calendar month).
    Period starts from billing_cycle_anchor day each month.
    
    Uses BIGINT for counters to handle high-volume customers.
    CHECK constraints prevent negative values (no refunds).
    """

    __tablename__ = "org_monthly_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False, index=True)  # Start of billing period
    period_end = Column(DateTime, nullable=False, index=True)  # End of billing period
    scans_used = Column(BigInteger, nullable=False, default=0)
    prompts_used = Column(BigInteger, nullable=False, default=0)
    ai_pages_generated = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("org_id", "period_start", name="uq_usage_org_period"),
        CheckConstraint("scans_used >= 0", name="ck_scans_non_negative"),
        CheckConstraint("prompts_used >= 0", name="ck_prompts_non_negative"),
        CheckConstraint("ai_pages_generated >= 0", name="ck_pages_non_negative"),
        # Composite index for efficient lookups (primary query pattern)
        Index("ix_org_monthly_usage_org_period", "org_id", "period_start"),
    )

    def __repr__(self) -> str:
        return f"<OrgMonthlyUsage(org_id={self.org_id}, period={self.period_start} to {self.period_end})>"

