"""Knowledge page schemas with strict validation."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models.knowledge_page import PageStatus


class KnowledgePageCreate(BaseModel):
    """Knowledge page creation schema with strict validation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    brand_id: int = Field(..., gt=0, description="Brand ID")
    title: str = Field(..., min_length=1, max_length=200, description="Page title")
    urls_to_crawl: Optional[List[HttpUrl]] = Field(None, max_length=10, description="URLs to crawl for content")
    vertical: str = Field(default="saas", min_length=1, max_length=50, description="Industry vertical")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate title."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class KnowledgePageUpdate(BaseModel):
    """Knowledge page update schema with strict validation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    mdx: Optional[str] = Field(None, max_length=100000)  # 100KB limit
    canonical_url: Optional[HttpUrl] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate title if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty")
        return v.strip() if v else None


class KnowledgePagePublish(BaseModel):
    """Knowledge page publish schema with strict validation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    subdomain: str = Field(..., min_length=1, max_length=63, pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")

    @field_validator("subdomain")
    @classmethod
    def validate_subdomain(cls, v):
        """Validate subdomain format."""
        v = v.lower().strip()
        if not v:
            raise ValueError("Subdomain cannot be empty")
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Subdomain cannot start or end with hyphen")
        return v


class KnowledgePageResponse(BaseModel):
    """Knowledge page response schema."""

    id: int
    brand_id: int
    title: str
    slug: str
    status: PageStatus
    score: Optional[float] = None
    published_at: Optional[datetime] = None
    canonical_url: Optional[str] = None
    path: Optional[str] = None
    subdomain: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgePageDetailResponse(KnowledgePageResponse):
    """Detailed knowledge page response with content."""

    html: Optional[str] = None
    mdx: Optional[str] = None
    schema_json: Optional[Dict[str, Any]] = None

