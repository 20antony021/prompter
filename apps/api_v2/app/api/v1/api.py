from fastapi import APIRouter
from app.api.v1.endpoints import topics, auth, webhooks

api_router = APIRouter()

api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
