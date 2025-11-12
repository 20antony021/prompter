"""
Page Cache Service

Redis-based caching for rendered pages to improve performance.
"""

from typing import Optional
import json
import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()


class PageCache:
    """Manages Redis caching for rendered pages."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client: Optional[redis.Redis] = None
        self.ttl = 3600  # 1 hour cache TTL
    
    async def connect(self):
        """Connect to Redis."""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get_page(self, subdomain: str, path: str) -> Optional[str]:
        """
        Get cached page HTML.
        
        Args:
            subdomain: Page subdomain
            path: Page path
            
        Returns:
            Cached HTML or None if not found
        """
        if not self.redis_client:
            await self.connect()
        
        cache_key = self._build_cache_key(subdomain, path)
        
        try:
            cached_html = await self.redis_client.get(cache_key)
            return cached_html
        except Exception as e:
            # Log error but don't fail - just skip cache
            print(f"Cache get error: {e}")
            return None
    
    async def set_page(self, subdomain: str, path: str, html: str, ttl: Optional[int] = None):
        """
        Cache page HTML.
        
        Args:
            subdomain: Page subdomain
            path: Page path
            html: Rendered HTML to cache
            ttl: Time to live in seconds (defaults to 1 hour)
        """
        if not self.redis_client:
            await self.connect()
        
        cache_key = self._build_cache_key(subdomain, path)
        ttl = ttl or self.ttl
        
        try:
            await self.redis_client.setex(cache_key, ttl, html)
        except Exception as e:
            # Log error but don't fail - just skip caching
            print(f"Cache set error: {e}")
    
    async def invalidate_page(self, subdomain: str, path: str):
        """
        Invalidate cached page.
        
        Args:
            subdomain: Page subdomain
            path: Page path
        """
        if not self.redis_client:
            await self.connect()
        
        cache_key = self._build_cache_key(subdomain, path)
        
        try:
            await self.redis_client.delete(cache_key)
        except Exception as e:
            print(f"Cache invalidate error: {e}")
    
    async def invalidate_subdomain(self, subdomain: str):
        """
        Invalidate all pages for a subdomain.
        
        Args:
            subdomain: Subdomain to invalidate
        """
        if not self.redis_client:
            await self.connect()
        
        pattern = f"page:{subdomain}:*"
        
        try:
            # Find all keys matching pattern
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete all matching keys
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache invalidate subdomain error: {e}")
    
    def _build_cache_key(self, subdomain: str, path: str) -> str:
        """Build Redis cache key."""
        # Normalize path
        path = path.strip('/')
        if not path:
            path = "index"
        
        return f"page:{subdomain}:{path}"
    
    async def get_sitemap(self, subdomain: str) -> Optional[str]:
        """
        Get cached sitemap XML.
        
        Args:
            subdomain: Subdomain
            
        Returns:
            Cached sitemap XML or None
        """
        if not self.redis_client:
            await self.connect()
        
        cache_key = f"sitemap:{subdomain}"
        
        try:
            return await self.redis_client.get(cache_key)
        except Exception as e:
            print(f"Sitemap cache get error: {e}")
            return None
    
    async def set_sitemap(self, subdomain: str, xml: str, ttl: int = 3600):
        """
        Cache sitemap XML.
        
        Args:
            subdomain: Subdomain
            xml: Sitemap XML content
            ttl: Time to live in seconds (default 1 hour)
        """
        if not self.redis_client:
            await self.connect()
        
        cache_key = f"sitemap:{subdomain}"
        
        try:
            await self.redis_client.setex(cache_key, ttl, xml)
        except Exception as e:
            print(f"Sitemap cache set error: {e}")

