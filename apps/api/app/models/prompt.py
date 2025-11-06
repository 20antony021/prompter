"""Prompt template and prompt set models."""
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.org import Org
    from app.models.scan import ScanRun


class PromptTemplate(Base):
    """Prompt template model."""

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=True)
    label = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    locale = Column(String(10), nullable=False, default="en")
    vertical = Column(String(100), nullable=True, index=True)  # SaaS, ecommerce, etc.
    is_system = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    org: "Org" = relationship("Org", back_populates="prompt_templates")
    prompt_set_items: List["PromptSetItem"] = relationship(
        "PromptSetItem", back_populates="prompt_template"
    )

    def __repr__(self) -> str:
        return f"<PromptTemplate(id={self.id}, label={self.label})>"


class PromptSet(Base):
    """Prompt set model - collection of prompts for a brand."""

    __tablename__ = "prompt_sets"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    brand: "Brand" = relationship("Brand", back_populates="prompt_sets")
    items: List["PromptSetItem"] = relationship("PromptSetItem", back_populates="prompt_set")
    scan_runs: List["ScanRun"] = relationship("ScanRun", back_populates="prompt_set")

    def __repr__(self) -> str:
        return f"<PromptSet(id={self.id}, name={self.name})>"


class PromptSetItem(Base):
    """Prompt set item - individual prompt in a set with variables."""

    __tablename__ = "prompt_set_items"

    id = Column(Integer, primary_key=True, index=True)
    prompt_set_id = Column(
        Integer, ForeignKey("prompt_sets.id", ondelete="CASCADE"), nullable=False
    )
    prompt_template_id = Column(
        Integer, ForeignKey("prompt_templates.id", ondelete="CASCADE"), nullable=False
    )
    variables_json = Column(JSON, nullable=True)  # Template variable substitutions
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    prompt_set: "PromptSet" = relationship("PromptSet", back_populates="items")
    prompt_template: "PromptTemplate" = relationship(
        "PromptTemplate", back_populates="prompt_set_items"
    )

    def __repr__(self) -> str:
        return f"<PromptSetItem(id={self.id}, prompt_set_id={self.prompt_set_id})>"

