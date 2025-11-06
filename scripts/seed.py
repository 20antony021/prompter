"""Seed database with demo data."""
import os
import sys
from datetime import datetime

# Add API to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../apps/api"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import (
    Brand,
    Competitor,
    KnowledgePage,
    Org,
    OrgMember,
    Plan,
    PromptSet,
    PromptSetItem,
    PromptTemplate,
    User,
)
from app.models.knowledge_page import PageStatus
from app.models.org import OrgRole, PlanTier

# Create engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def seed_plans(db):
    """Seed subscription plans."""
    plans = [
        Plan(
            code="starter",
            name="Starter",
            price_monthly=4900,  # $49
            limits_json={
                "prompts_per_month": 100,
                "pages": 5,
                "seats": 3,
                "scans_per_day": 10,
            },
        ),
        Plan(
            code="growth",
            name="Growth",
            price_monthly=14900,  # $149
            limits_json={
                "prompts_per_month": 500,
                "pages": 25,
                "seats": 10,
                "scans_per_day": 50,
            },
        ),
        Plan(
            code="enterprise",
            name="Enterprise",
            price_monthly=49900,  # $499
            limits_json={
                "prompts_per_month": -1,  # unlimited
                "pages": -1,
                "seats": -1,
                "scans_per_day": -1,
            },
        ),
    ]

    for plan in plans:
        existing = db.query(Plan).filter(Plan.code == plan.code).first()
        if not existing:
            db.add(plan)
            print(f"Created plan: {plan.name}")

    db.commit()


def seed_demo_org(db):
    """Seed demo organization with data."""
    # Create demo user
    user = User(
        auth_provider_id="demo_user_123",
        email="demo@prompter.site",
        name="Demo User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created user: {user.email}")

    # Create demo org
    org = Org(
        name="Acme CRM",
        slug="acme-crm",
        plan_tier=PlanTier.GROWTH,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    print(f"Created org: {org.name}")

    # Add user as owner
    org_member = OrgMember(
        org_id=org.id,
        user_id=user.id,
        role=OrgRole.OWNER,
    )
    db.add(org_member)
    db.commit()

    # Create brand
    brand = Brand(
        org_id=org.id,
        name="AcmeCRM",
        website="https://acmecrm.example.com",
        primary_domain="acmecrm.example.com",
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)
    print(f"Created brand: {brand.name}")

    # Add competitors
    competitors = [
        Competitor(
            brand_id=brand.id,
            name="SalesFlow",
            website="https://salesflow.example.com",
        ),
        Competitor(
            brand_id=brand.id,
            name="PipeTrack",
            website="https://pipetrack.example.com",
        ),
        Competitor(
            brand_id=brand.id,
            name="CRM360",
            website="https://crm360.example.com",
        ),
    ]

    for competitor in competitors:
        db.add(competitor)
        print(f"Created competitor: {competitor.name}")

    db.commit()

    # Create prompt templates
    templates = [
        PromptTemplate(
            org_id=org.id,
            label="Best CRM for small business",
            text="What is the best CRM software for small businesses in 2024?",
            vertical="saas",
        ),
        PromptTemplate(
            org_id=org.id,
            label="CRM comparison",
            text="Compare the top 5 CRM platforms for sales teams.",
            vertical="saas",
        ),
        PromptTemplate(
            org_id=org.id,
            label="Affordable CRM",
            text="Which CRM is most affordable for startups?",
            vertical="saas",
        ),
        PromptTemplate(
            org_id=org.id,
            label="CRM features",
            text="What features should I look for in a CRM system?",
            vertical="saas",
        ),
        PromptTemplate(
            org_id=org.id,
            label="CRM recommendations",
            text="Can you recommend a good CRM for a B2B sales team?",
            vertical="saas",
        ),
    ]

    for template in templates:
        db.add(template)
        print(f"Created template: {template.label}")

    db.commit()

    # Create prompt set
    prompt_set = PromptSet(
        brand_id=brand.id,
        name="CRM Industry Scan",
        description="Standard prompts for CRM industry visibility",
    )
    db.add(prompt_set)
    db.commit()
    db.refresh(prompt_set)
    print(f"Created prompt set: {prompt_set.name}")

    # Add templates to set
    for template in templates:
        item = PromptSetItem(
            prompt_set_id=prompt_set.id,
            prompt_template_id=template.id,
        )
        db.add(item)

    db.commit()

    # Create knowledge page
    page = KnowledgePage(
        brand_id=brand.id,
        title="AcmeCRM - Modern CRM for Growing Teams",
        slug="acmecrm-modern-crm",
        status=PageStatus.PUBLISHED,
        html="<div><h2>AcmeCRM Overview</h2><p>AcmeCRM is a modern customer relationship management platform designed for growing sales teams.</p></div>",
        mdx="## AcmeCRM Overview\n\nAcmeCRM is a modern customer relationship management platform designed for growing sales teams.",
        schema_json={
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "AcmeCRM",
            "description": "Modern CRM for growing teams",
        },
        score=85.5,
        published_at=datetime.utcnow(),
        path="/k/acmecrm-modern-crm",
        subdomain="acme",
    )
    db.add(page)
    db.commit()
    print(f"Created knowledge page: {page.title}")

    print("\n✅ Demo data seeded successfully!")
    print(f"\nDemo account:")
    print(f"  Email: {user.email}")
    print(f"  Org: {org.name}")
    print(f"  Brand: {brand.name}")
    print(f"  Competitors: {len(competitors)}")
    print(f"  Prompt templates: {len(templates)}")
    print(f"  Knowledge pages: 1")


def main():
    """Main seed function."""
    print("🌱 Seeding database...")

    db = SessionLocal()

    try:
        # Seed plans
        seed_plans(db)

        # Seed demo org
        seed_demo_org(db)

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()

