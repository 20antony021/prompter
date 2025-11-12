from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from fastapi import Depends
import json
from typing import Optional
import logging
from svix.webhooks import Webhook, WebhookVerificationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def verify_svix_signature(payload: bytes, headers: dict, secret: str) -> bool:
    """
    Verify Svix webhook signature using official Svix SDK
    """
    try:
        svix_id = headers.get("svix-id")
        svix_timestamp = headers.get("svix-timestamp")
        svix_signature = headers.get("svix-signature")
        
        logger.info(f"🔐 Verifying signature with Svix SDK...")
        logger.info(f"  svix-id: {svix_id}")
        logger.info(f"  svix-timestamp: {svix_timestamp}")
        logger.info(f"  svix-signature: {svix_signature[:50]}..." if svix_signature and len(svix_signature) > 50 else f"  svix-signature: {svix_signature}")
        logger.info(f"  secret configured: {'Yes' if secret else 'No'}")
        
        if not secret:
            logger.error("❌ CLERK_WEBHOOK_SECRET not configured!")
            return False
        
        if not all([svix_id, svix_timestamp, svix_signature]):
            logger.warning("❌ Missing required Svix headers")
            return False
        
        # Use official Svix SDK for verification
        wh = Webhook(secret)
        
        # Svix SDK expects headers as a dict with specific keys
        headers_dict = {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        }
        
        # Verify and parse the webhook payload
        wh.verify(payload, headers_dict)
        
        logger.info("✅ Signature verified successfully with Svix SDK!")
        return True
        
    except WebhookVerificationError as e:
        logger.error(f"❌ Webhook verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error verifying signature: {e}", exc_info=True)
        return False


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    db: Session = Depends(get_db),
    svix_id: Optional[str] = Header(None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
):
    """
    Handle Clerk webhook events
    
    Supported events:
    - user.created: Create user in database when registered
    - user.updated: Update user information
    - user.deleted: Mark user as deleted (soft delete)
    """
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify webhook signature in production
    if settings.CLERK_WEBHOOK_SECRET:
        headers = {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature
        }
        
        if not verify_svix_signature(body, headers, settings.CLERK_WEBHOOK_SECRET):
            logger.error("Webhook signature verification failed")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )
        logger.info("Webhook signature verified successfully")
    else:
        logger.warning("CLERK_WEBHOOK_SECRET not set - skipping signature verification (DEV MODE ONLY)")
    
    try:
        data = json.loads(body)
        event_type = data.get("type")
        event_data = data.get("data", {})
        
        if event_type == "user.created":
            logger.info(f"Processing user.created event")
            # Extract user information from Clerk
            user_id = event_data.get("id")
            email_addresses = event_data.get("email_addresses", [])
            primary_email = None
            
            # Find primary email
            for email in email_addresses:
                if email.get("id") == event_data.get("primary_email_address_id"):
                    primary_email = email.get("email_address")
                    break
            
            if not primary_email and email_addresses:
                primary_email = email_addresses[0].get("email_address")
            
            # Get user name
            first_name = event_data.get("first_name", "")
            last_name = event_data.get("last_name", "")
            name = f"{first_name} {last_name}".strip() or "User"
            
            logger.info(f"Creating user: {user_id}, email: {primary_email}, name: {name}")
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.id == user_id).first()
            
            if not existing_user:
                # Create new user
                new_user = User(
                    id=user_id,
                    email=primary_email or f"{user_id}@clerk.user",
                    name=name,
                    email_verified=event_data.get("email_verified", False),
                    image=event_data.get("image_url"),
                    plan="free",
                    plan_status="active"
                )
                db.add(new_user)
                db.commit()
                
                logger.info(f"✅ User created successfully: {user_id}")
                return {
                    "status": "success",
                    "message": "User created",
                    "user_id": user_id
                }
            else:
                logger.info(f"User already exists: {user_id}")
                return {
                    "status": "success",
                    "message": "User already exists",
                    "user_id": user_id
                }
        
        elif event_type == "user.updated":
            user_id = event_data.get("id")
            user = db.query(User).filter(User.id == user_id).first()
            
            if user:
                # Update user information
                email_addresses = event_data.get("email_addresses", [])
                for email in email_addresses:
                    if email.get("id") == event_data.get("primary_email_address_id"):
                        user.email = email.get("email_address")
                        break
                
                first_name = event_data.get("first_name", "")
                last_name = event_data.get("last_name", "")
                if first_name or last_name:
                    user.name = f"{first_name} {last_name}".strip()
                
                if "image_url" in event_data:
                    user.image = event_data.get("image_url")
                
                user.email_verified = event_data.get("email_verified", user.email_verified)
                
                db.commit()
                
                return {
                    "status": "success",
                    "message": "User updated",
                    "user_id": user_id
                }
            else:
                # User doesn't exist, create it
                return await clerk_webhook(request, db, svix_id, svix_timestamp, svix_signature)
        
        elif event_type == "user.deleted":
            user_id = event_data.get("id")
            user = db.query(User).filter(User.id == user_id).first()
            
            if user:
                # Soft delete: you might want to add a 'deleted_at' column
                # For now, we'll just return success
                # db.delete(user)  # Hard delete (not recommended)
                # db.commit()
                
                return {
                    "status": "success",
                    "message": "User deletion noted",
                    "user_id": user_id
                }
        
        return {
            "status": "success",
            "message": f"Event {event_type} received but not processed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Webhook processing error: {str(e)}"
        )
