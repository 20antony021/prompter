"""Scan run and scan result models."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.mention import Mention
    from app.models.prompt import PromptSet


class ScanStatus(str, Enum):
    """Scan run status."""

    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class ScanRun(Base):
    """Scan run model - a batch of prompts across multiple models."""

    __tablename__ = "scan_runs"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    prompt_set_id = Column(
        Integer, ForeignKey("prompt_sets.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(SQLEnum(ScanStatus), nullable=False, default=ScanStatus.QUEUED, index=True)
    model_matrix_json = Column(
        JSON, nullable=False
    )  # List of models to test: ["gpt-4", "claude-3", ...]
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    brand: "Brand" = relationship("Brand", back_populates="scan_runs")
    prompt_set: "PromptSet" = relationship("PromptSet", back_populates="scan_runs")
    results: List["ScanResult"] = relationship("ScanResult", back_populates="scan_run")

    def __repr__(self) -> str:
        return f"<ScanRun(id={self.id}, status={self.status})>"


class ScanResult(Base):
    """Scan result model - single prompt response from a model."""

    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_run_id = Column(Integer, ForeignKey("scan_runs.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False, index=True)
    prompt_text = Column(Text, nullable=False)
    raw_response = Column(Text, nullable=False)
    parsed_json = Column(JSON, nullable=True)  # Structured extraction results
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    scan_run: "ScanRun" = relationship("ScanRun", back_populates="results")
    mentions: List["Mention"] = relationship("Mention", back_populates="scan_result")

    def __repr__(self) -> str:
        return f"<ScanResult(id={self.id}, model={self.model_name})>"

