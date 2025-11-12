from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.db.session import Base


class ModelEnum(str, enum.Enum):
    openai = "openai"
    claude = "claude"
    google = "google"


class GeoRegionEnum(str, enum.Enum):
    global_ = "global"
    us = "us"
    eu = "eu"
    uk = "uk"
    de = "de"
    fr = "fr"
    es = "es"
    it = "it"
    in_ = "in"
    jp = "jp"
    cn = "cn"
    au = "au"
    ca = "ca"
    br = "br"
    mx = "mx"
    ar = "ar"
    sa = "sa"
    ae = "ae"
    il = "il"
    tr = "tr"


class StatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class MentionTypeEnum(str, enum.Enum):
    direct = "direct"
    indirect = "indirect"
    competitive = "competitive"


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    logo = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="topics")
    prompts = relationship("Prompt", back_populates="topic", cascade="all, delete-orphan")
    mentions = relationship("Mention", back_populates="topic", cascade="all, delete-orphan")


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.pending)
    geo_region = Column(SQLEnum(GeoRegionEnum), nullable=False, default=GeoRegionEnum.global_)
    visibility_score = Column(Numeric(5, 2), nullable=True)
    tags = Column(JSONB, nullable=False, default=list)
    prompt_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    topic = relationship("Topic", back_populates="prompts")
    user = relationship("User", back_populates="prompts")
    model_results = relationship("ModelResult", back_populates="prompt", cascade="all, delete-orphan")
    mentions = relationship("Mention", back_populates="prompt", cascade="all, delete-orphan")


class ModelResult(Base):
    __tablename__ = "prompt_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    model = Column(SQLEnum(ModelEnum), nullable=False)
    response_metadata = Column(JSONB, nullable=False, default=dict)
    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.pending)
    error_message = Column(Text, nullable=True)
    results = Column(JSONB, nullable=False, default=list)
    sources = Column(JSONB, nullable=True, default=list)
    citations = Column(JSONB, nullable=True, default=list)
    search_queries = Column(JSONB, nullable=True, default=list)
    grounding_metadata = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    prompt = relationship("Prompt", back_populates="model_results")
    mentions = relationship("Mention", back_populates="model_result", cascade="all, delete-orphan")


class Mention(Base):
    __tablename__ = "mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    model_result_id = Column(UUID(as_uuid=True), ForeignKey("prompt_results.id", ondelete="CASCADE"), nullable=False)
    model = Column(SQLEnum(ModelEnum), nullable=False)
    mention_type = Column(SQLEnum(MentionTypeEnum), nullable=False)
    position = Column(Numeric, nullable=True)
    context = Column(Text, nullable=False)
    sentiment = Column(SQLEnum(SentimentEnum), nullable=False)
    confidence = Column(Numeric(3, 2), nullable=True)
    extracted_text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    prompt = relationship("Prompt", back_populates="mentions")
    topic = relationship("Topic", back_populates="mentions")
    model_result = relationship("ModelResult", back_populates="mentions")
