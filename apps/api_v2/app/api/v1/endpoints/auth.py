from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.clerk_auth import get_current_user, get_optional_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user information"""
    # Update fields
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/sync-clerk")
async def sync_clerk_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync user data from Clerk (webhook endpoint)"""
    # This endpoint would be called by Clerk webhooks to sync user data
    # For now, just return success
    return {"message": "User synced successfully", "user_id": current_user.id}
