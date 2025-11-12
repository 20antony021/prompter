from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class TopicBase(BaseModel):
    name: str
    logo: Optional[str] = None
    description: Optional[str] = None


class TopicCreate(TopicBase):
    pass


class TopicCreateFromUrl(BaseModel):
    url: str


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TopicResponse(TopicBase):
    id: UUID
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptBase(BaseModel):
    content: str
    geo_region: str = "global"
    tags: List[str] = []
    metadata: dict = {}


class PromptCreate(PromptBase):
    topic_id: UUID


class PromptUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
    geo_region: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class PromptResponse(PromptBase):
    id: UUID
    topic_id: UUID
    user_id: str
    status: str
    visibility_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TopicSuggestion(BaseModel):
    id: str
    name: str
    description: str
    category: str
