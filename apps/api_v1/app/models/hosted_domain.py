"""Hosted domain models for custom subdomains."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.org import Org


class DnsStatus(str, Enum):
    """DNS configuration status."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class HostedDomain(Base):
    """Hosted domain model - custom domains for hosting pages."""

    __tablename__ = "hosted_domains"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    apex_domain = Column(String(255), nullable=False, index=True)
    wildcard_enabled = Column(Boolean, nullable=False, default=False)
    dns_status = Column(SQLEnum(DnsStatus), nullable=False, default=DnsStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    org: "Org" = relationship("Org", back_populates="hosted_domains")
    site_bindings: List["HostedSiteBinding"] = relationship(
        "HostedSiteBinding", back_populates="hosted_domain"
    )

    def __repr__(self) -> str:
        return f"<HostedDomain(id={self.id}, apex_domain={self.apex_domain})>"


class HostedSiteBinding(Base):
    """Hosted site binding - maps brand to subdomain."""

    __tablename__ = "hosted_site_bindings"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    hosted_domain_id = Column(
        Integer, ForeignKey("hosted_domains.id", ondelete="CASCADE"), nullable=False
    )
    subdomain = Column(String(255), nullable=False, index=True)  # e.g., "acme"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    brand: "Brand" = relationship("Brand", back_populates="hosted_site_bindings")
    hosted_domain: "HostedDomain" = relationship(
        "HostedDomain", back_populates="site_bindings"
    )

    def __repr__(self) -> str:
        return f"<HostedSiteBinding(id={self.id}, subdomain={self.subdomain})>"

