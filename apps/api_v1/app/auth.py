"""Authentication and authorization utilities."""
import logging
from typing import Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.org import OrgMember, OrgRole
from app.models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer()


class JWKSCache:
    """Cache for JWKS keys."""

    def __init__(self):
        self.keys = None
        self.last_fetch = 0

    async def get_keys(self):
        """Fetch JWKS keys with caching."""
        import time

        current_time = time.time()
        if self.keys is None or (current_time - self.last_fetch) > 3600:  # 1 hour cache
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.CLERK_JWKS_URL)
                response.raise_for_status()
                jwks_data = response.json()
                self.keys = jwks_data["keys"]
                self.last_fetch = current_time
        return self.keys


jwks_cache = JWKSCache()


async def verify_jwt_token(token: str) -> dict:
    """
    Verify JWT token from Clerk.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Get JWKS keys
        keys = await jwks_cache.get_keys()

        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find matching key
        key = None
        for k in keys:
            if k["kid"] == kid:
                key = jwt.algorithms.RSAAlgorithm.from_jwk(k)
                break

        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: Key not found",
            )

        # Verify and decode token
        payload = jwt.decode(
            token,
            key=key,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user and set request state for rate limiting.

    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If user not found or unauthorized
    """
    token = credentials.credentials
    payload = await verify_jwt_token(token)

    # Get user ID from token (Clerk uses 'sub')
    auth_provider_id = payload.get("sub")
    if not auth_provider_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Find or create user
    user = db.query(User).filter(User.auth_provider_id == auth_provider_id).first()

    if not user:
        # Create user from token data
        email = payload.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not found in token",
            )

        user = User(
            auth_provider_id=auth_provider_id,
            email=email,
            name=payload.get("name"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Set user in request state for rate limiting
    request.state.user = user

    return user


class CurrentOrgMember:
    """Dependency to get current org member with role validation."""

    def __init__(self, required_roles: Optional[list[OrgRole]] = None):
        """
        Initialize with required roles.

        Args:
            required_roles: List of roles allowed to access the endpoint
        """
        self.required_roles = required_roles or [OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MEMBER]

    async def __call__(
        self,
        org_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> OrgMember:
        """
        Get current organization member.

        Args:
            org_id: Organization ID
            current_user: Current authenticated user
            db: Database session

        Returns:
            Organization member

        Raises:
            HTTPException: If user is not a member or lacks required role
        """
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
                detail="Not a member of this organization",
            )

        if org_member.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {self.required_roles}",
            )

        return org_member


# Convenience functions for common role checks
def require_owner() -> CurrentOrgMember:
    """Require owner role."""
    return CurrentOrgMember(required_roles=[OrgRole.OWNER])


def require_admin() -> CurrentOrgMember:
    """Require owner or admin role."""
    return CurrentOrgMember(required_roles=[OrgRole.OWNER, OrgRole.ADMIN])


def require_member() -> CurrentOrgMember:
    """Require any member role."""
    return CurrentOrgMember(required_roles=[OrgRole.OWNER, OrgRole.ADMIN, OrgRole.MEMBER])

