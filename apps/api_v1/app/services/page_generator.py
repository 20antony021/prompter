"""Knowledge page generation service."""
import json
import logging
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from slugify import slugify

from app.llm_providers import get_provider
from app.models.brand import Brand

logger = logging.getLogger(__name__)


class PageGenerator:
    """Generate AI-optimized knowledge pages."""

    def __init__(self, brand: Brand):
        """
        Initialize page generator.

        Args:
            brand: Brand to generate page for
        """
        self.brand = brand

    async def generate_page(
        self,
        title: str,
        urls_to_crawl: Optional[List[str]] = None,
        vertical: str = "saas",
    ) -> Dict[str, any]:
        """
        Generate knowledge page.

        Args:
            title: Page title
            urls_to_crawl: List of URLs to crawl for content
            vertical: Business vertical (saas, ecommerce, fintech, etc.)

        Returns:
            Dictionary with page content (html, mdx, schema, score)
        """
        # Step 1: Crawl and extract content
        facts = await self._extract_facts(urls_to_crawl or [self.brand.website])

        # Step 2: Generate structured content using LLM
        content = await self._generate_content(title, facts, vertical)

        # Step 3: Generate JSON-LD schema
        schema = self._generate_schema(title, content, vertical)

        # Step 4: Convert MDX to HTML
        html = self._mdx_to_html(content["mdx"])

        # Step 5: Calculate page health score
        score = self._calculate_page_score(html, schema)

        return {
            "title": title,
            "slug": slugify(title),
            "mdx": content["mdx"],
            "html": html,
            "schema_json": schema,
            "score": score,
        }

    async def _extract_facts(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        Extract facts from URLs.

        Args:
            urls: List of URLs to crawl

        Returns:
            List of fact dictionaries
        """
        facts = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for url in urls[:5]:  # Limit to 5 URLs
                try:
                    response = await client.get(url)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer"]):
                        script.decompose()

                    # Extract text
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = " ".join(chunk for chunk in chunks if chunk)

                    # Truncate
                    text = text[:5000]

                    facts.append({"source": url, "content": text, "type": "webpage"})

                except Exception as e:
                    logger.warning(f"Failed to crawl {url}: {e}")

        return facts

    async def _generate_content(
        self, title: str, facts: List[Dict[str, str]], vertical: str
    ) -> Dict[str, str]:
        """
        Generate page content using LLM.

        Args:
            title: Page title
            facts: Extracted facts
            vertical: Business vertical

        Returns:
            Dictionary with content
        """
        # Combine facts into context
        context = "\n\n".join(
            [f"Source: {fact['source']}\n{fact['content']}" for fact in facts]
        )

        system_prompt = """You are an expert content writer creating AI-optimized knowledge pages.
Your goal is to create structured, factual content that helps AI assistants understand and recommend products/services.

Guidelines:
- Be factual and cite sources
- Use clear, structured format with headers
- Include bullet points for key features
- Add FAQ section
- Keep it concise but comprehensive
- Optimize for AI readability"""

        user_prompt = f"""Create a comprehensive knowledge page about: {title}

Vertical: {vertical}

Context from brand website:
{context[:3000]}

Generate an MDX document with the following sections:
1. Summary (2-3 sentences)
2. Key Features (bullet points)
3. Use Cases
4. Pricing (if available)
5. Comparisons (key differentiators)
6. FAQ (3-5 common questions)

Format as MDX with proper headers (##, ###) and markdown."""

        provider = get_provider("gpt-4")
        response = await provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2000,
        )

        return {"mdx": response.text}

    def _generate_schema(
        self, title: str, content: Dict[str, str], vertical: str
    ) -> Dict:
        """
        Generate JSON-LD schema.

        Args:
            title: Page title
            content: Page content
            vertical: Business vertical

        Returns:
            JSON-LD schema dictionary
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Product" if vertical in ["saas", "ecommerce"] else "Organization",
            "name": title,
            "description": self.brand.name,
            "url": self.brand.website,
        }

        # Add FAQ schema if content has FAQs
        if "faq" in content["mdx"].lower():
            schema["mainEntity"] = {
                "@type": "FAQPage",
                "name": f"{title} - Frequently Asked Questions",
            }

        return schema

    def _mdx_to_html(self, mdx: str) -> str:
        """
        Convert MDX to HTML (simple markdown conversion).

        Args:
            mdx: MDX content

        Returns:
            HTML string
        """
        # For production, use a proper MDX processor
        # This is a simplified version
        html = mdx

        # Convert headers
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", 1)

        # Convert lists
        lines = html.split("\n")
        in_list = False
        processed_lines = []

        for line in lines:
            if line.startswith("- "):
                if not in_list:
                    processed_lines.append("<ul>")
                    in_list = True
                processed_lines.append(f"<li>{line[2:]}</li>")
            else:
                if in_list:
                    processed_lines.append("</ul>")
                    in_list = False
                processed_lines.append(line)

        if in_list:
            processed_lines.append("</ul>")

        html = "\n".join(processed_lines)

        # Wrap in paragraphs
        html = f"<div class='prose'>{html}</div>"

        return html

    def _calculate_page_score(self, html: str, schema: Dict) -> float:
        """
        Calculate page health score.

        Args:
            html: HTML content
            schema: JSON-LD schema

        Returns:
            Score (0-100)
        """
        score = 0.0

        # Content length (0-25 points)
        content_length = len(html)
        if content_length > 500:
            score += min(25, content_length / 100)

        # Has structured data (25 points)
        if schema and "@type" in schema:
            score += 25

        # Has headers (25 points)
        if "<h2>" in html or "<h3>" in html:
            score += 25

        # Has lists (25 points)
        if "<ul>" in html or "<ol>" in html:
            score += 25

        return min(100.0, score)

