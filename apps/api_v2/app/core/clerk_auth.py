from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from jwt import PyJWKClient
from typing import Optional
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
import uuid

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_clerk_jwks_url() -> str:
    """Get Clerk's JWKS URL for JWT verification"""
    # 优先使用配置的 JWKS URL
    if settings.CLERK_JWKS_URL:
        return settings.CLERK_JWKS_URL
    
    # 如果没有配置，从 CLERK_PUBLISHABLE_KEY 提取实例 ID
    if not settings.CLERK_PUBLISHABLE_KEY:
        raise ValueError("CLERK_PUBLISHABLE_KEY not set")
    
    # Clerk publishable key 格式: pk_test_<base64>
    # 需要从 Clerk Dashboard 获取完整的 JWKS URL
    # 或使用环境变量 CLERK_JWKS_URL
    raise ValueError(
        "CLERK_JWKS_URL not configured. "
        "Please set CLERK_JWKS_URL in your .env file. "
        "Find it in Clerk Dashboard → API Keys → Advanced → JWKS URL"
    )


def _verify_with_public_key(token: str, public_key_raw: str) -> Optional[dict]:
    """Verify token with a provided RSA public key (PEM or base64 body)."""
    if not public_key_raw:
        return None
    # Accept raw base64 without PEM headers and wrap if needed
    if "BEGIN PUBLIC KEY" not in public_key_raw:
        public_key_raw = "-----BEGIN PUBLIC KEY-----\n" + public_key_raw + "\n-----END PUBLIC KEY-----"
    try:
        decoded = jwt.decode(
            token,
            public_key_raw,
            algorithms=["RS256"],
            options={"verify_exp": True},
        )
        return decoded
    except Exception:
        return None


async def verify_clerk_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    """Verify Clerk JWT token and return user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    
    try:
        # For development, you can skip verification if needed
        if not settings.CLERK_SECRET_KEY:
            # Extract user info from token without verification (dev only)
            unverified = jwt.decode(token, options={"verify_signature": False})
            user_id = unverified.get("sub")
        else:
            # Production: Verify with Clerk's JWKS
            decoded = None
            try:
                jwks_url = get_clerk_jwks_url()
                jwks_client = PyJWKClient(jwks_url)
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                decoded = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256"],
                    options={"verify_exp": True}
                )
            except Exception:
                # Fallback: try explicit public key if provided
                if settings.CLERK_JWT_VERIFICATION_KEY:
                    decoded = _verify_with_public_key(token, settings.CLERK_JWT_VERIFICATION_KEY)
            if not decoded:
                raise HTTPException(status_code=401, detail="Invalid token")
            user_id = decoded.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get or create user in our database
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            # Create user from Clerk data
            # In production, you'd want to fetch full user data from Clerk API
            user = User(
                id=user_id,
                email=f"{user_id}@clerk.user",  # Temporary, should fetch from Clerk
                name="Clerk User",  # Should fetch from Clerk
                email_verified=True,
                plan="free",
                plan_status="active"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


async def get_current_user(
    user: User = Depends(verify_clerk_token)
) -> User:
    """Dependency to get current authenticated user"""
    return user


async def get_optional_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security)
) -> Optional[User]:
    """Dependency to get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        
        # For development, you can skip verification if needed
        if not settings.CLERK_SECRET_KEY:
            unverified = jwt.decode(token, options={"verify_signature": False})
            user_id = unverified.get("sub")
        else:
            jwks_url = get_clerk_jwks_url()
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_exp": True}
            )
            user_id = decoded.get("sub")
        
        if not user_id:
            return None
        
        # Get or create user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                email=f"{user_id}@clerk.user",
                name="Clerk User",
                email_verified=True,
                plan="free",
                plan_status="active"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
    except Exception:
        return None
