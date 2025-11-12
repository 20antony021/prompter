"""Pagination schemas and utilities."""
import base64
import json
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Cursor-based pagination parameters.
    
    Cursor-based pagination is preferred over offset-based for:
    - Better performance on large datasets
    - Consistent results even as data changes
    - Avoids missing/duplicate items
    """

    limit: int = Field(default=50, ge=1, le=100, description="Number of items to return")
    cursor: Optional[str] = Field(default=None, description="Opaque cursor for next page")

    @field_validator("cursor")
    @classmethod
    def validate_cursor(cls, v):
        """Validate and decode cursor."""
        if v is None:
            return None
        try:
            # Cursors are base64-encoded JSON
            decoded = base64.b64decode(v).decode("utf-8")
            cursor_data = json.loads(decoded)
            return cursor_data
        except Exception:
            raise ValueError("Invalid cursor format")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response envelope.
    
    Contains:
    - items: List of results
    - next_cursor: Cursor for next page (None if last page)
    - has_more: Boolean indicating if more results exist
    """

    items: List[T]
    next_cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    has_more: bool = Field(default=False, description="Whether more results exist")

    class Config:
        """Pydantic config."""

        from_attributes = True


def encode_cursor(last_id: int, last_created_at: Optional[str] = None) -> str:
    """
    Encode cursor from last item.
    
    Args:
        last_id: ID of last item in current page
        last_created_at: created_at timestamp of last item (for time-based sorting)
    
    Returns:
        Base64-encoded cursor string
    """
    cursor_data = {"id": last_id}
    if last_created_at:
        cursor_data["created_at"] = last_created_at

    cursor_json = json.dumps(cursor_data)
    cursor_bytes = cursor_json.encode("utf-8")
    cursor_b64 = base64.b64encode(cursor_bytes).decode("utf-8")

    return cursor_b64


def decode_cursor(cursor: Optional[str]) -> Optional[dict]:
    """
    Decode cursor string.
    
    Args:
        cursor: Base64-encoded cursor string
    
    Returns:
        Decoded cursor data dict or None
    """
    if not cursor:
        return None

    try:
        cursor_bytes = base64.b64decode(cursor)
        cursor_json = cursor_bytes.decode("utf-8")
        cursor_data = json.loads(cursor_json)
        return cursor_data
    except Exception:
        return None

