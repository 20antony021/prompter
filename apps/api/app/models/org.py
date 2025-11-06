"""Organization models."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.hosted_domain import HostedDomain
    from app.models.plan import UsageMeter
    from app.models.prompt import PromptTemplate
    from app.models.user import ApiKey, User


class OrgRole(str, Enum):
    """Organization member roles."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class PlanTier(str, Enum):
    """Subscription plan tiers."""

    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class Org(Base):
    """Organization model."""

    __tablename__ = "orgs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    plan_tier = Column(
        SQLEnum(PlanTier), nullable=False, default=PlanTier.STARTER, index=True
    )
    seats_limit = Column(Integer, nullable=True)  # NULL means unlimited (Business+)
    billing_cycle_anchor = Column(Integer, nullable=False, default=1)  # Day of month (1-31) when billing cycle starts
    current_period_start = Column(DateTime, nullable=True)  # Start of current billing period
    current_period_end = Column(DateTime, nullable=True)  # End of current billing period
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    members: List["OrgMember"] = relationship("OrgMember", back_populates="org")
    brands: List["Brand"] = relationship("Brand", back_populates="org")
    prompt_templates: List["PromptTemplate"] = relationship(
        "PromptTemplate", back_populates="org"
    )
    hosted_domains: List["HostedDomain"] = relationship("HostedDomain", back_populates="org")
    usage_meters: List["UsageMeter"] = relationship("UsageMeter", back_populates="org")
    api_keys: List["ApiKey"] = relationship("ApiKey", back_populates="org")

    def __repr__(self) -> str:
        return f"<Org(id={self.id}, name={self.name}, slug={self.slug})>"


class OrgMember(Base):
    """Organization member model."""

    __tablename__ = "org_members"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(OrgRole), nullable=False, default=OrgRole.MEMBER)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    org: "Org" = relationship("Org", back_populates="members")
    user: "User" = relationship("User", back_populates="org_members")

    def __repr__(self) -> str:
        return f"<OrgMember(org_id={self.org_id}, user_id={self.user_id}, role={self.role})>"

