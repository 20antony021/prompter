from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    image: Optional[str] = None


class UserResponse(UserBase):
    id: str
    email_verified: bool
    image: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    plan: str
    plan_status: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
    stripe_current_period_end: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    token: str
    expires_at: datetime
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True
