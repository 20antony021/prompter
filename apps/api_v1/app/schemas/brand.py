"""Brand schemas with strict validation."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class CompetitorBase(BaseModel):
    """Base competitor schema with strict validation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    name: str = Field(..., min_length=1, max_length=200, description="Competitor name")
    website: HttpUrl = Field(..., description="Competitor website URL")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate competitor name."""
        if not v or not v.strip():
            raise ValueError("Competitor name cannot be empty")
        return v.strip()


class CompetitorCreate(CompetitorBase):
    """Competitor creation schema."""

    pass


class CompetitorResponse(CompetitorBase):
    """Competitor response schema."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    brand_id: int
    created_at: datetime


class BrandBase(BaseModel):
    """Base brand schema with strict validation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    name: str = Field(..., min_length=1, max_length=200, description="Brand name")
    website: HttpUrl = Field(..., description="Brand website URL")
    primary_domain: Optional[str] = Field(None, max_length=255, description="Primary domain for hosting")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate brand name."""
        if not v or not v.strip():
            raise ValueError("Brand name cannot be empty")
        return v.strip()

    @field_validator("primary_domain")
    @classmethod
    def validate_domain(cls, v):
        """Validate domain format."""
        if v is not None and v.strip():
            v = v.strip().lower()
            # Basic domain validation
            if not v or len(v) > 255:
                raise ValueError("Invalid domain")
            # Remove protocol if present
            if "://" in v:
                v = v.split("://", 1)[1]
            # Remove path if present
            if "/" in v:
                v = v.split("/", 1)[0]
            return v
        return None


class BrandCreate(BrandBase):
    """Brand creation schema."""

    org_id: int = Field(..., gt=0, description="Organization ID")


class BrandUpdate(BaseModel):
    """Brand update schema - all fields optional."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    website: Optional[HttpUrl] = None
    primary_domain: Optional[str] = Field(None, max_length=255)


class BrandResponse(BrandBase):
    """Brand response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    created_at: datetime
    competitors: List[CompetitorResponse] = []

