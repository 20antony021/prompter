"""
SEO Endpoints

Public endpoints for serving knowledge pages, sitemaps, and robots.txt.
These endpoints do not require authentication.

Uses host-based routing to extract subdomain from the Host header.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.knowledge_page import KnowledgePage
from app.models.brand import Brand
from app.services.page_renderer import PageRenderer
from app.services.page_cache import PageCache
from app.services.schema_validator import SchemaValidator

router = APIRouter()


# Initialize services
page_renderer = PageRenderer()
page_cache = PageCache()
schema_validator = SchemaValidator()


def extract_subdomain(request: Request) -> Optional[str]:
    """
    Extract subdomain from the Host header.
    
    Examples:
        - brand.prompter.site -> "brand"
        - localhost:8000 -> None
        - prompter.site -> None
    
    Args:
        request: FastAPI request object
        
    Returns:
        Subdomain string or None if not a subdomain request
    """
    host = request.headers.get("host", "")
    
    # Remove port if present
    host = host.split(":")[0]
    
    # Check if it's a subdomain of prompter.site
    if host.endswith(".prompter.site"):
        # Extract subdomain (everything before .prompter.site)
        subdomain = host.replace(".prompter.site", "")
        return subdomain if subdomain else None
    
    return None


async def serve_page_internal(
    subdomain: str,
    path: str,
    db: AsyncSession
) -> Response:
    """
    Internal function to serve a published knowledge page.
    
    Args:
        subdomain: Page subdomain (e.g., "acme")
        path: Page path (e.g., "/product-guide")
        db: Database session
        
    Returns:
        HTML page with full SEO tags
    """
    # Normalize path
    path = path.strip('/')
    if not path:
        path = "index"
    
    # Try to get from cache first
    cached_html = await page_cache.get_page(subdomain, path)
    if cached_html:
        return Response(
            content=cached_html,
            media_type="text/html",
            headers={
                "X-Cache": "HIT",
                "Cache-Control": "public, max-age=3600"
            }
        )
    
    # Query database for page
    query = (
        select(KnowledgePage)
        .where(
            and_(
                KnowledgePage.subdomain == subdomain,
                KnowledgePage.path == path,
                KnowledgePage.status == 'published'
            )
        )
    )
    
    result = await db.execute(query)
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page not found: {subdomain}/{path}"
        )
    
    # Build canonical URL from subdomain and path
    canonical_url = page.canonical_url or f"https://{subdomain}.prompter.site/{path}"
    
    # Get page HTML (if already rendered) or render it
    if page.html:
        html = page.html
    else:
        # Render from MDX if HTML not available
        html = page_renderer.render_html(
            title=page.title,
            content_html=page.mdx,  # In production, convert MDX to HTML
            meta_description=None,  # Will be auto-generated
            canonical_url=canonical_url,
            schema_json=page.schema_json,
            og_image=None,
            published_at=page.published_at,
            updated_at=page.updated_at
        )
    
    # Cache the HTML
    await page_cache.set_page(subdomain, path, html)
    
    return Response(
        content=html,
        media_type="text/html",
        headers={
            "X-Cache": "MISS",
            "Cache-Control": "public, max-age=3600"
        }
    )


@router.get("/{path:path}", response_class=Response)
async def serve_page_by_host(
    path: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Serve a published knowledge page using host-based routing.
    
    The subdomain is extracted from the Host header (e.g., brand.prompter.site).
    This is the main endpoint for serving pages at https://brand.prompter.site/path
    
    Args:
        path: Page path (from URL path)
        request: FastAPI request (to extract Host header)
        db: Database session
        
    Returns:
        HTML page with full SEO tags
    """
    # Extract subdomain from Host header
    subdomain = extract_subdomain(request)
    
    if not subdomain:
        raise HTTPException(
            status_code=400,
            detail="Invalid host. Pages must be accessed via subdomain (e.g., brand.prompter.site)"
        )
    
    # Check if this is a sitemap or robots.txt request
    if path == "sitemap.xml":
        return await get_sitemap_by_host(request, db)
    elif path == "robots.txt":
        return await get_robots_by_host(request)
    
    # Serve the page
    return await serve_page_internal(subdomain, path, db)


async def get_sitemap_by_host(
    request: Request,
    db: AsyncSession
) -> Response:
    """
    Generate sitemap.xml for published pages on this subdomain.
    
    Accessible at https://brand.prompter.site/sitemap.xml
    
    Args:
        request: FastAPI request (to extract Host header)
        db: Database session
        
    Returns:
        XML sitemap for this subdomain
    """
    # Extract subdomain from Host header
    subdomain = extract_subdomain(request)
    
    if not subdomain:
        raise HTTPException(
            status_code=400,
            detail="Invalid host. Sitemap must be accessed via subdomain (e.g., brand.prompter.site/sitemap.xml)"
        )
    
    # Try to get from cache
    cached_sitemap = await page_cache.get_sitemap(subdomain)
    if cached_sitemap:
        return Response(
            content=cached_sitemap,
            media_type="application/xml",
            headers={"X-Cache": "HIT", "Cache-Control": "public, max-age=3600"}
        )
    
    # Query published pages for this subdomain
    query = (
        select(KnowledgePage)
        .where(
            and_(
                KnowledgePage.status == 'published',
                KnowledgePage.subdomain == subdomain
            )
        )
    )
    
    result = await db.execute(query)
    pages = result.scalars().all()
    
    # Generate sitemap XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        # Build URL using subdomain-based format
        if page.canonical_url:
            url = page.canonical_url
        else:
            # Construct URL from subdomain and path
            url = f"https://{subdomain}.prompter.site/{page.path}"
        
        # Format dates
        lastmod = page.updated_at or page.published_at
        lastmod_str = lastmod.strftime('%Y-%m-%d') if lastmod else ''
        
        # Determine change frequency and priority
        # Pages updated recently have higher priority
        if lastmod:
            days_since_update = (datetime.utcnow() - lastmod).days
            if days_since_update < 7:
                changefreq = 'daily'
                priority = '0.9'
            elif days_since_update < 30:
                changefreq = 'weekly'
                priority = '0.7'
            else:
                changefreq = 'monthly'
                priority = '0.5'
        else:
            changefreq = 'weekly'
            priority = '0.5'
        
        xml += '  <url>\n'
        xml += f'    <loc>{url}</loc>\n'
        if lastmod_str:
            xml += f'    <lastmod>{lastmod_str}</lastmod>\n'
        xml += f'    <changefreq>{changefreq}</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += '  </url>\n'
    
    xml += '</urlset>'
    
    # Cache the sitemap
    await page_cache.set_sitemap(subdomain, xml)
    
    return Response(
        content=xml,
        media_type="application/xml",
        headers={
            "X-Cache": "MISS",
            "Cache-Control": "public, max-age=3600"
        }
    )


async def get_robots_by_host(request: Request) -> Response:
    """
    Generate robots.txt for AI crawlers on this subdomain.
    
    Accessible at https://brand.prompter.site/robots.txt
    
    Args:
        request: FastAPI request (to extract Host header)
        
    Returns:
        robots.txt content
    """
    # Extract subdomain from Host header
    subdomain = extract_subdomain(request)
    
    if not subdomain:
        raise HTTPException(
            status_code=400,
            detail="Invalid host. Robots.txt must be accessed via subdomain (e.g., brand.prompter.site/robots.txt)"
        )
    
    # Build robots.txt
    robots = "# Robots.txt for Prompter Knowledge Pages\n\n"
    
    # Allow all crawlers
    robots += "User-agent: *\n"
    robots += "Allow: /\n\n"
    
    # Specific rules for AI crawlers
    ai_crawlers = [
        "GPTBot",  # OpenAI
        "ChatGPT-User",  # ChatGPT
        "Google-Extended",  # Google AI
        "CCBot",  # Common Crawl (used by AI)
        "anthropic-ai",  # Anthropic
        "Claude-Web",  # Claude
        "PerplexityBot",  # Perplexity
        "Amazonbot",  # Amazon
        "Applebot-Extended",  # Apple AI
        "cohere-ai",  # Cohere
    ]
    
    for crawler in ai_crawlers:
        robots += f"User-agent: {crawler}\n"
        robots += "Allow: /\n"
        robots += "Crawl-delay: 1\n\n"
    
    # Add sitemap reference for this subdomain
    robots += f"Sitemap: https://{subdomain}.prompter.site/sitemap.xml\n"
    
    return Response(
        content=robots,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )


@router.post("/v1/pages/{page_id}/invalidate-cache")
async def invalidate_page_cache(
    page_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Invalidate cache for a specific page.
    
    This should be called whenever a page is updated or republished.
    
    Args:
        page_id: Page ID
        db: Database session
        
    Returns:
        Success message
    """
    # Get page
    query = select(KnowledgePage).where(KnowledgePage.id == page_id)
    result = await db.execute(query)
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Invalidate cache
    await page_cache.invalidate_page(page.subdomain, page.path)
    
    # Also invalidate sitemap
    await page_cache.invalidate_subdomain(page.subdomain)
    
    return {
        "status": "success",
        "message": f"Cache invalidated for {page.subdomain}/{page.path}"
    }


@router.post("/v1/subdomains/{subdomain}/invalidate-cache")
async def invalidate_subdomain_cache(subdomain: str):
    """
    Invalidate all cached pages for a subdomain.
    
    Args:
        subdomain: Subdomain to invalidate
        
    Returns:
        Success message
    """
    await page_cache.invalidate_subdomain(subdomain)
    
    return {
        "status": "success",
        "message": f"Cache invalidated for subdomain: {subdomain}"
    }

