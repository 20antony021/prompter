"""Scan schemas with strict validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.scan import ScanStatus


class ScanRunCreate(BaseModel):
    """Scan run creation schema with strict validation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    brand_id: int = Field(..., gt=0, description="Brand ID to scan")
    prompt_set_id: int = Field(..., gt=0, description="Prompt set ID to use")
    models: List[str] = Field(..., min_length=1, max_length=10, description="List of model keys to test")

    @field_validator("models")
    @classmethod
    def validate_models(cls, v):
        """Validate model list."""
        if not v or len(v) == 0:
            raise ValueError("At least one model must be specified")
        
        # Validate each model key
        valid_prefixes = ["gpt-", "gemini", "perplexity", "claude", "llama"]
        for model in v:
            if not any(model.startswith(prefix) for prefix in valid_prefixes):
                raise ValueError(f"Invalid model key: {model}")
        
        return v


class ScanRunResponse(BaseModel):
    """Scan run response schema."""

    id: int
    brand_id: int
    prompt_set_id: int
    status: ScanStatus
    model_matrix_json: List[str]
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResultResponse(BaseModel):
    """Scan result response schema."""

    id: int
    scan_run_id: int
    model_name: str
    prompt_text: str
    raw_response: str
    parsed_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MentionResponse(BaseModel):
    """Mention response schema."""

    id: int
    scan_result_id: int
    entity_name: str
    entity_type: str
    sentiment: Optional[float] = None
    position_index: Optional[int] = None
    confidence: Optional[float] = None
    cited_urls_json: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanRunDetailResponse(ScanRunResponse):
    """Detailed scan run response with results."""

    results: List[ScanResultResponse] = []

