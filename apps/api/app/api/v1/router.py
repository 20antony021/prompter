"""API v1 router."""
from fastapi import APIRouter

from app.api.v1.endpoints import analytics, brands, orgs, pages, scans, usage

api_router = APIRouter()

api_router.include_router(brands.router, prefix="/brands", tags=["brands"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router.include_router(orgs.router, prefix="/orgs", tags=["organizations"])

