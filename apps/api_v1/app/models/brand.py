"""Brand and competitor models."""
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.hosted_domain import HostedSiteBinding
    from app.models.knowledge_page import KnowledgePage
    from app.models.org import Org
    from app.models.prompt import PromptSet
    from app.models.scan import ScanRun


class Brand(Base):
    """Brand model."""

    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    website = Column(String(500), nullable=False)
    primary_domain = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    org: "Org" = relationship("Org", back_populates="brands")
    competitors: List["Competitor"] = relationship("Competitor", back_populates="brand")
    prompt_sets: List["PromptSet"] = relationship("PromptSet", back_populates="brand")
    scan_runs: List["ScanRun"] = relationship("ScanRun", back_populates="brand")
    knowledge_pages: List["KnowledgePage"] = relationship("KnowledgePage", back_populates="brand")
    hosted_site_bindings: List["HostedSiteBinding"] = relationship(
        "HostedSiteBinding", back_populates="brand"
    )

    def __repr__(self) -> str:
        return f"<Brand(id={self.id}, name={self.name})>"


class Competitor(Base):
    """Competitor model."""

    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    website = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    brand: "Brand" = relationship("Brand", back_populates="competitors")

    def __repr__(self) -> str:
        return f"<Competitor(id={self.id}, name={self.name})>"

