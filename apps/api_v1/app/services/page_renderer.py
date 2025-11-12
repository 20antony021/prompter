"""
Page Renderer Service

Handles HTML rendering for published knowledge pages with full SEO optimization.
"""

from typing import Dict, Optional
from datetime import datetime
import json


class PageRenderer:
    """Renders knowledge pages with full SEO tags and structured data."""
    
    def __init__(self):
        """Initialize the page renderer."""
        pass
    
    def render_html(
        self,
        title: str,
        content_html: str,
        meta_description: Optional[str] = None,
        canonical_url: Optional[str] = None,
        schema_json: Optional[Dict] = None,
        og_image: Optional[str] = None,
        published_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> str:
        """
        Render a complete HTML page with full SEO tags.
        
        Args:
            title: Page title
            content_html: Main content HTML
            meta_description: Meta description (auto-generated if None)
            canonical_url: Canonical URL for the page
            schema_json: JSON-LD structured data
            og_image: Open Graph image URL
            published_at: Publication date
            updated_at: Last updated date
            
        Returns:
            Complete HTML document as string
        """
        # Auto-generate meta description if not provided
        if not meta_description:
            meta_description = self._generate_meta_description(content_html)
        
        # Prepare dates
        published_iso = published_at.isoformat() if published_at else ""
        updated_iso = updated_at.isoformat() if updated_at else ""
        
        # Build schema JSON-LD
        schema_tag = ""
        if schema_json:
            schema_tag = f'<script type="application/ld+json">{json.dumps(schema_json, indent=2)}</script>'
        
        # Build Open Graph tags
        og_tags = self._build_og_tags(
            title=title,
            description=meta_description,
            url=canonical_url,
            image=og_image,
            published_at=published_iso,
            updated_at=updated_iso,
        )
        
        # Build Twitter Card tags
        twitter_tags = self._build_twitter_tags(
            title=title,
            description=meta_description,
            image=og_image,
        )
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(title)}</title>
    
    <!-- Basic Meta Tags -->
    <meta name="description" content="{self._escape_html(meta_description)}">
    {f'<link rel="canonical" href="{canonical_url}">' if canonical_url else ''}
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    
    <!-- Date Meta Tags -->
    {f'<meta property="article:published_time" content="{published_iso}">' if published_iso else ''}
    {f'<meta property="article:modified_time" content="{updated_iso}">' if updated_iso else ''}
    
    <!-- Open Graph Tags -->
    {og_tags}
    
    <!-- Twitter Card Tags -->
    {twitter_tags}
    
    <!-- JSON-LD Structured Data -->
    {schema_tag}
    
    <!-- Styles -->
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #fff;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 20px;
            color: #1a1a1a;
        }}
        
        h2 {{
            font-size: 2em;
            margin-top: 40px;
            margin-bottom: 15px;
            color: #2a2a2a;
        }}
        
        h3 {{
            font-size: 1.5em;
            margin-top: 30px;
            margin-bottom: 10px;
            color: #3a3a3a;
        }}
        
        p {{
            margin-bottom: 15px;
        }}
        
        ul, ol {{
            margin-bottom: 15px;
            margin-left: 25px;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin-bottom: 15px;
        }}
        
        blockquote {{
            border-left: 4px solid #0066cc;
            padding-left: 20px;
            margin: 20px 0;
            color: #555;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            margin: 20px 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: #f4f4f4;
            font-weight: 600;
        }}
        
        .meta-info {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                padding: 20px 10px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
            
            h3 {{
                font-size: 1.2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <article>
            <h1>{self._escape_html(title)}</h1>
            {self._build_meta_info(published_iso, updated_iso)}
            <div class="content">
                {content_html}
            </div>
        </article>
    </div>
    
    <!-- Prompter Branding (Subtle) -->
    <footer style="text-align: center; margin-top: 60px; padding: 20px; color: #999; font-size: 0.85em;">
        <p>Powered by <a href="https://prompter.site" style="color: #666;">Prompter</a></p>
    </footer>
</body>
</html>"""
        
        return html
    
    def _build_og_tags(
        self,
        title: str,
        description: str,
        url: Optional[str],
        image: Optional[str],
        published_at: str,
        updated_at: str,
    ) -> str:
        """Build Open Graph meta tags."""
        tags = [
            f'<meta property="og:type" content="article">',
            f'<meta property="og:title" content="{self._escape_html(title)}">',
            f'<meta property="og:description" content="{self._escape_html(description)}">',
        ]
        
        if url:
            tags.append(f'<meta property="og:url" content="{url}">')
        
        if image:
            tags.append(f'<meta property="og:image" content="{image}">')
            tags.append(f'<meta property="og:image:alt" content="{self._escape_html(title)}">')
        
        if published_at:
            tags.append(f'<meta property="article:published_time" content="{published_at}">')
        
        if updated_at:
            tags.append(f'<meta property="article:modified_time" content="{updated_at}">')
        
        return '\n    '.join(tags)
    
    def _build_twitter_tags(
        self,
        title: str,
        description: str,
        image: Optional[str],
    ) -> str:
        """Build Twitter Card meta tags."""
        tags = [
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{self._escape_html(title)}">',
            f'<meta name="twitter:description" content="{self._escape_html(description)}">',
        ]
        
        if image:
            tags.append(f'<meta name="twitter:image" content="{image}">')
        
        return '\n    '.join(tags)
    
    def _build_meta_info(self, published_at: str, updated_at: str) -> str:
        """Build meta information section."""
        if not published_at and not updated_at:
            return ""
        
        parts = []
        if published_at:
            try:
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                parts.append(f"Published: {dt.strftime('%B %d, %Y')}")
            except:
                pass
        
        if updated_at and updated_at != published_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                parts.append(f"Updated: {dt.strftime('%B %d, %Y')}")
            except:
                pass
        
        if parts:
            return f'<div class="meta-info">{" | ".join(parts)}</div>'
        return ""
    
    def _generate_meta_description(self, html: str, max_length: int = 155) -> str:
        """Generate meta description from HTML content."""
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean up whitespace
        text = ' '.join(text.split())
        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'
        return text
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;')
        )

