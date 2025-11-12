"""Organization and member management endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.deps.quotas import check_seats_available
from app.models.org import Org, OrgMember, OrgRole
from app.models.user import User

router = APIRouter()


class MemberResponse(BaseModel):
    """Organization member response."""
    
    id: int
    user_id: int
    email: str
    name: str | None
    role: str
    created_at: str
    
    class Config:
        from_attributes = True


class InviteMemberRequest(BaseModel):
    """Request to invite a new member."""
    
    email: EmailStr
    role: OrgRole = OrgRole.MEMBER


class UpdateMemberRequest(BaseModel):
    """Request to update member role."""
    
    role: OrgRole


@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def list_members(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all members of an organization.
    
    Requires user to be a member of the organization.
    """
    # Verify user is member of the org
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )
    
    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization",
        )
    
    # Get all members
    members = (
        db.query(OrgMember)
        .filter(OrgMember.org_id == org_id)
        .join(User)
        .all()
    )
    
    return [
        MemberResponse(
            id=member.id,
            user_id=member.user_id,
            email=member.user.email,
            name=member.user.name,
            role=member.role.value,
            created_at=member.created_at.isoformat(),
        )
        for member in members
    ]


@router.post("/{org_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: int,
    invite_data: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Invite a new member to the organization.
    
    Requires user to be an owner or admin.
    Enforces seat limits based on plan.
    """
    # Verify user is admin/owner of the org
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )
    
    if not org_member or org_member.role.value not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can invite members",
        )
    
    # Check seats quota
    check_seats_available(org_id, db)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    
    if existing_user:
        # Check if already a member
        existing_member = (
            db.query(OrgMember)
            .filter(
                OrgMember.org_id == org_id,
                OrgMember.user_id == existing_user.id,
            )
            .first()
        )
        
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization",
            )
        
        # Add existing user to org
        new_member = OrgMember(
            org_id=org_id,
            user_id=existing_user.id,
            role=invite_data.role,
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        
        return MemberResponse(
            id=new_member.id,
            user_id=existing_user.id,
            email=existing_user.email,
            name=existing_user.name,
            role=new_member.role.value,
            created_at=new_member.created_at.isoformat(),
        )
    else:
        # In production, this would send an invite email
        # For now, we'll create a placeholder user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Invite email functionality not implemented yet.",
        )


@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a member from the organization.
    
    Requires user to be an owner or admin.
    Cannot remove yourself.
    """
    # Verify user is admin/owner of the org
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == org_id,
            OrgMember.user_id == current_user.id,
        )
        .first()
    )
    
    if not org_member or org_member.role.value not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can remove members",
        )
    
    # Get member to remove
    member_to_remove = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    
    if not member_to_remove or member_to_remove.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    
    # Cannot remove yourself
    if member_to_remove.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the organization",
        )
    
    # Cannot remove owner
    if member_to_remove.role == OrgRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove organization owner",
        )
    
    db.delete(member_to_remove)
    db.commit()


@router.patch("/{org_id}/members/{member_id}", response_model=MemberResponse)
async def update_member_role(
    org_id: int,
    member_id: int,
    update_data: UpdateMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a member's role.
    
    Requires user to be an owner.
    """
    # Verify user is owner of the org
    org_member = (
        db.query(OrgMember)
        .filter(
            OrgMember.org_id == org_id,
            OrgMember.user_id == current_user.id,
            OrgMember.role == OrgRole.OWNER,
        )
        .first()
    )
    
    if not org_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can update member roles",
        )
    
    # Get member to update
    member_to_update = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    
    if not member_to_update or member_to_update.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    
    # Update role
    member_to_update.role = update_data.role
    db.commit()
    db.refresh(member_to_update)
    
    return MemberResponse(
        id=member_to_update.id,
        user_id=member_to_update.user_id,
        email=member_to_update.user.email,
        name=member_to_update.user.name,
        role=member_to_update.role.value,
        created_at=member_to_update.created_at.isoformat(),
    )

