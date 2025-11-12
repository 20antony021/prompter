from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from typing import List, Optional
from uuid import UUID
import re
import json
from typing import Any
import requests
import html
import uuid
import random

from app.db.session import get_db
from app.core.config import settings
from app.core.clerk_auth import get_current_user
from app.models.user import User
from app.models.topic import Topic, Prompt
from app.schemas.topic import (
    TopicResponse,
    TopicCreate,
    TopicCreateFromUrl,
    TopicUpdate,
    PromptCreate,
    PromptResponse,
    TopicSuggestion,
)

router = APIRouter()


def _fetch_html(url: str) -> Optional[str]:
    try:
        resp = requests.get(
            url,
            timeout=8,
            headers={
                "User-Agent": "Mozilla/5.0",
            },
        )
        if 200 <= resp.status_code < 400:
            return resp.text
    except Exception:
        return None
    return None


def _extract_meta_value(text: str, keys: List[str]) -> Optional[str]:
    for key in keys:
        m = re.search(r'<meta[^>]+name=["\']' + re.escape(key) + r'["\'][^>]*content=["\']([^"\']{1,500})["\']', text, flags=re.I | re.S)
        if m:
            return html.unescape(m.group(1)).strip()
        m = re.search(r'<meta[^>]+property=["\']' + re.escape(key) + r'["\'][^>]*content=["\']([^"\']{1,500})["\']', text, flags=re.I | re.S)
        if m:
            return html.unescape(m.group(1)).strip()
    return None


def _extract_title_value(text: str) -> Optional[str]:
    m = re.search(r'<title[^>]*>(.*?)</title>', text, flags=re.I | re.S)
    if m:
        return html.unescape(m.group(1)).strip()
    return None


def _infer_name_and_description(domain: str):
    for scheme in ["https://", "http://"]:
        for host in [domain, f"www.{domain}"]:
            html_text = _fetch_html(scheme + host)
            if not html_text:
                continue
            name = _extract_meta_value(html_text, ["og:site_name", "application-name", "og:title", "twitter:title"])
            if not name:
                t = _extract_title_value(html_text)
                if t:
                    name = re.split(r"[\-|–|\|]", t)[0].strip()
            # sanitize long titles like "Brand | Tagline"
            if name:
                name = re.split(r"\s*[\-|–|\|]\s*", name)[0].strip()
            desc = _extract_meta_value(html_text, ["og:description", "twitter:description", "description"])
            if desc:
                desc = re.sub(r"\s+", " ", desc).strip()
            if name or desc:
                return name, desc
    return None, None


 


def clean_url(url: str) -> str:
    """Extract clean domain from URL"""
    # Remove protocol
    url = re.sub(r'^https?://', '', url)
    # Remove www.
    url = re.sub(r'^www\.', '', url)
    # Remove trailing slash and path
    url = url.split('/')[0]
    return url


def check_topic_limit(user: User, db: Session) -> dict:
    """Check if user can create more topics based on their plan"""
    topic_count = db.query(Topic).filter(Topic.user_id == user.id).count()
    
    # Read limits from settings to allow environment overrides in development
    limits = {
        "free": settings.TOPIC_LIMIT_FREE,
        "basic": settings.TOPIC_LIMIT_BASIC,
        "pro": settings.TOPIC_LIMIT_PRO,
        "enterprise": settings.TOPIC_LIMIT_ENTERPRISE,
    }
    
    limit = limits.get(user.plan, settings.TOPIC_LIMIT_FREE)
    can_create = limit == -1 or topic_count < limit
    
    return {
        "can_create_topic": can_create,
        "current_count": topic_count,
        "limit": limit
    }


@router.get("/", response_model=List[TopicResponse])
async def get_topics(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all topics for current user, optionally filtered by search query"""
    query = db.query(Topic).filter(Topic.user_id == current_user.id)

    if q:
        like = f"%{q}%"
        # Only filter by topic name as requested
        query = query.filter(Topic.name.ilike(like))

    topics = query.order_by(Topic.created_at.desc()).all()

    return topics


@router.post("/", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic_data: TopicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new topic"""
    # Check topic limit
    limit_check = check_topic_limit(current_user, db)
    if not limit_check["can_create_topic"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You've reached your limit of {limit_check['limit']} topics. Upgrade your plan."
        )
    
    topic = Topic(
        name=topic_data.name,
        logo=topic_data.logo,
        description=topic_data.description,
        user_id=current_user.id
    )
    
    db.add(topic)
    db.commit()
    db.refresh(topic)
    
    return topic


@router.post("/from-url", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic_from_url(
    topic_data: TopicCreateFromUrl,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new topic from URL"""
    # Check topic limit
    limit_check = check_topic_limit(current_user, db)
    if not limit_check["can_create_topic"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You've reached your limit of {limit_check['limit']} topics. Upgrade your plan."
        )
    
    
    domain = clean_url(topic_data.url)
    inferred_name, inferred_desc = _infer_name_and_description(domain)
    base = domain.split('.')[0]
    name = (inferred_name or re.sub(r'[^A-Za-z0-9]+', ' ', base).strip().title()) or base
    description = (inferred_desc or f"Insights for {name}").strip()
    
    topic = Topic(
        name=name,
        logo=domain,
        description=description,
        user_id=current_user.id
    )
    
    db.add(topic)
    db.commit()
    db.refresh(topic)
    
    # TODO: Create auto-prompts in background
    
    return topic


# Place the suggestions endpoint before dynamic '/{topic_id}' routes to avoid
# path matching to the UUID route which can cause 422 errors.

@router.get("/suggestions", response_model=List[TopicSuggestion])
async def get_topic_suggestions(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate topic suggestions via LLM (auth required).

    If OPENAI_API_KEY is not configured or the call fails, returns a small fallback list.
    """
    prompt_query = q or "marketing and technology"
    seed_hint = uuid.uuid4().hex[:8]
    system = (
        "You are a helpful assistant that proposes interesting brands/companies to analyze. "
        "Respond in English only. Return a JSON object with a 'suggestions' array of 12 items. Each item has id, name, category, description."
    )
    user = (
        "Suggest 12 brands or companies (well-known and emerging) relevant to: '" + prompt_query + "'. "
        "Each description should be rich and specific in 1-2 sentences, highlighting industry, flagship products, audience, and why they are interesting for SEO/marketing analysis. "
        "Provide a varied mix across categories and avoid repeating the exact same set on different calls. Randomness hint: "
        + seed_hint
    )

    content = _openai_chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=0.9)

    if content:
        parsed = _parse_suggestions_json(content)
        if parsed:
            return parsed

    # Fallback if no LLM or parse failure
    return random.sample(FALLBACK_SUGGESTIONS, k=len(FALLBACK_SUGGESTIONS))


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific topic"""
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return topic


@router.patch("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID,
    topic_data: TopicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a topic"""
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Update fields
    for field, value in topic_data.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    
    db.commit()
    db.refresh(topic)
    
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a topic"""
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    db.delete(topic)
    db.commit()
    
    return None


@router.get("/{topic_id}/prompts", response_model=List[PromptResponse])
async def get_topic_prompts(
    topic_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all prompts for a topic"""
    # Verify topic belongs to user
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    prompts = db.query(Prompt).filter(
        Prompt.topic_id == topic_id
    ).order_by(Prompt.created_at.desc()).all()
    
    return prompts


# ----------------------
# Suggestions via LLM
# ----------------------

FALLBACK_SUGGESTIONS: List[TopicSuggestion] = [
    TopicSuggestion(
        id="fallback_1",
        name="Shopify",
        description="A leading e‑commerce platform powering millions of merchants worldwide. Strong app ecosystem, robust SEO tooling, and educational content make it a benchmark for product-led growth and merchant acquisition strategies.",
        category="E-commerce",
    ),
    TopicSuggestion(
        id="fallback_2",
        name="Tesla",
        description="Pioneer of electric vehicles and energy solutions. Known for direct-to-consumer sales, bold brand storytelling, and viral product launches that set trends in automotive marketing and community engagement.",
        category="Automotive",
    ),
    TopicSuggestion(
        id="fallback_3",
        name="Notion",
        description="All‑in‑one workspace with viral community adoption. Excels at SEO through templates, internationalization, and creator partnerships that drive organic discovery and retention in productivity software.",
        category="SaaS",
    ),
    TopicSuggestion(
        id="fallback_4",
        name="Netflix",
        description="Global streaming leader that popularized binge watching. Its data‑driven personalization, original content branding, and subscription lifecycle tactics offer rich lessons for growth and retention marketing.",
        category="Streaming Entertainment",
    ),
    TopicSuggestion(
        id="fallback_5",
        name="Asana",
        description="Project management platform for teams. A model for B2B SEO at scale, feature‑led onboarding, and multi‑persona messaging across SMB and enterprise segments in a competitive SaaS category.",
        category="Project Management Software",
    ),
    TopicSuggestion(
        id="fallback_6",
        name="Salesforce",
        description="Dominant CRM vendor with a vast ecosystem. Demonstrates enterprise content strategy, multi‑product cross‑sell motions, and event‑driven brand building around Dreamforce and industry cloud offerings.",
        category="CRM Software",
    ),
    TopicSuggestion(
        id="fallback_7",
        name="Airbnb",
        description="Marketplace for stays and experiences. Blends community storytelling with scalable SEO on location pages and trust signals, shaping how peer‑to‑peer platforms drive both supply and demand.",
        category="Travel",
    ),
    TopicSuggestion(
        id="fallback_8",
        name="Google",
        description="Search and AI company defining consumer discovery. Offers insights into SERP feature evolution, product surfaces like Maps and YouTube, and platform effects on brand visibility and performance.",
        category="Technology",
    ),
    TopicSuggestion(
        id="fallback_9",
        name="Amazon",
        description="Commerce and cloud giant. Reveals marketplace SEO dynamics, logistics‑driven conversion strategy, and Prime‑centric retention that influence how brands compete for high‑intent traffic.",
        category="E-commerce",
    ),
    TopicSuggestion(
        id="fallback_10",
        name="Microsoft",
        description="Diversified technology leader across cloud, productivity, and AI. Showcases multi‑brand navigation, enterprise developer marketing, and integration plays from Windows to Azure and Copilot.",
        category="Technology",
    ),
    TopicSuggestion(
        id="fallback_11",
        name="NVIDIA",
        description="Semiconductor and AI infrastructure powerhouse. Illustrates category creation around GPUs, platform ecosystems with CUDA, and thought leadership in AI research driving enterprise demand.",
        category="Semiconductors",
    ),
    TopicSuggestion(
        id="fallback_12",
        name="TikTok",
        description="Short‑video platform shaping culture and commerce. Provides a lens on creator‑led growth, algorithmic discovery, and social shopping features that brands leverage for awareness and conversion.",
        category="Social Media",
    ),
]


def _openai_chat(messages: List[dict], model: Optional[str] = None, temperature: float = 0.5) -> Optional[str]:
    """Call OpenAI's Chat Completions API directly via HTTP. Returns content or None."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return None

    model = model or settings.OPENAI_MODEL or "gpt-4o-mini"
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": temperature,
                "messages": messages,
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
        return content
    except Exception:
        return None


def _parse_suggestions_json(raw: str) -> List[TopicSuggestion]:
    try:
        obj = json.loads(raw)
        items = obj.get("suggestions") if isinstance(obj, dict) else obj
        results: List[TopicSuggestion] = []
        if isinstance(items, list):
            for idx, it in enumerate(items):
                if not isinstance(it, dict):
                    continue
                name = str(it.get("name", "")).strip()
                if not name:
                    continue
                results.append(
                    TopicSuggestion(
                        id=str(it.get("id") or f"llm_{idx}"),
                        name=name,
                        description=str(it.get("description", "")).strip() or "",
                        category=str(it.get("category", "")).strip() or "General",
                    )
                )
        return results
    except Exception:
        return []

 
