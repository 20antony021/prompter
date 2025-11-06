"""Seed database with sample data for testing."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models.brand import Brand, Competitor
from app.models.knowledge_page import KnowledgePage, PageStatus
from app.models.mention import Mention
from app.models.org import Org, PlanTier
from app.models.scan import ScanResult, ScanRun, ScanStatus
from app.models.user import User


def seed_database():
    """Seed database with sample data."""
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_org = db.query(Org).first()
        if existing_org:
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding database with sample data...")

        # Create organization
        org = Org(
            name="Acme Corporation",
            slug="acme-corp",
            plan_tier=PlanTier.STARTER,
        )
        db.add(org)
        db.flush()

        # Create user (would normally come from Clerk)
        user = User(
            clerk_id="user_demo123",
            email="demo@acmecorp.com",
            name="Demo User",
        )
        db.add(user)
        db.flush()

        # Create brand
        brand = Brand(
            org_id=org.id,
            name="AcmeCRM",
            website="https://acmecrm.com",
            primary_domain="acmecrm.com",
        )
        db.add(brand)
        db.flush()

        print(f"Created brand: {brand.name} (ID: {brand.id})")

        # Create competitors
        competitors = [
            Competitor(
                brand_id=brand.id,
                name="SalesFlow",
                website="https://salesflow.com",
            ),
            Competitor(
                brand_id=brand.id,
                name="CRMPro",
                website="https://crmpro.com",
            ),
            Competitor(
                brand_id=brand.id,
                name="LeadMaster",
                website="https://leadmaster.com",
            ),
        ]
        for comp in competitors:
            db.add(comp)
        db.flush()

        print(f"Created {len(competitors)} competitors")

        # Create scan runs
        now = datetime.utcnow()
        scan_runs = []

        for i in range(3):
            scan_run = ScanRun(
                brand_id=brand.id,
                status=ScanStatus.COMPLETED,
                created_at=now - timedelta(days=i * 2),
                completed_at=now - timedelta(days=i * 2, hours=-1),
                model_matrix_json=["gpt-4", "perplexity-sonar", "gemini-pro"],
            )
            db.add(scan_run)
            db.flush()
            scan_runs.append(scan_run)

        print(f"Created {len(scan_runs)} scan runs")

        # Create scan results and mentions
        mention_data = [
            {
                "entity": "AcmeCRM",
                "sentiment": 0.8,
                "position": 0,
                "context": "AcmeCRM is a leading CRM solution...",
            },
            {
                "entity": "AcmeCRM",
                "sentiment": 0.7,
                "position": 1,
                "context": "For small businesses, AcmeCRM offers...",
            },
            {
                "entity": "SalesFlow",
                "sentiment": 0.6,
                "position": 2,
                "context": "SalesFlow is another option...",
            },
            {
                "entity": "CRMPro",
                "sentiment": 0.5,
                "position": 3,
                "context": "CRMPro provides enterprise features...",
            },
            {
                "entity": "AcmeCRM",
                "sentiment": 0.9,
                "position": 0,
                "context": "The best CRM for startups is AcmeCRM...",
            },
        ]

        total_mentions = 0
        for scan_run in scan_runs:
            for model in scan_run.model_matrix_json:
                # Create scan result
                scan_result = ScanResult(
                    scan_run_id=scan_run.id,
                    model_name=model,
                    prompt_text="What is the best CRM software for small businesses?",
                    response_text="Based on current options, here are the top CRM solutions...",
                    response_time_ms=1500,
                )
                db.add(scan_result)
                db.flush()

                # Create mentions for this result
                for mention_info in mention_data[:3]:  # Add 3 mentions per result
                    mention = Mention(
                        scan_result_id=scan_result.id,
                        entity_name=mention_info["entity"],
                        entity_type="brand",
                        mention_text=mention_info["context"],
                        position=mention_info["position"],
                        sentiment_score=mention_info["sentiment"],
                        context_before="When looking at CRM options,",
                        context_after="which makes it a great choice.",
                        created_at=scan_run.created_at,
                    )
                    db.add(mention)
                    total_mentions += 1

        print(f"Created {total_mentions} mentions")

        # Create knowledge pages
        pages = [
            KnowledgePage(
                brand_id=brand.id,
                title="AcmeCRM Product Overview",
                slug="acmecrm-product-overview",
                status=PageStatus.PUBLISHED,
                mdx="# AcmeCRM Product Overview\n\nLearn about our comprehensive CRM solution...",
                subdomain="acme",
                path="/k/acmecrm-product-overview",
                published_at=now - timedelta(days=10),
            ),
            KnowledgePage(
                brand_id=brand.id,
                title="Best CRM for Small Business",
                slug="best-crm-small-business",
                status=PageStatus.PUBLISHED,
                mdx="# Best CRM for Small Business\n\nDiscover why AcmeCRM is the top choice...",
                subdomain="acme",
                path="/k/best-crm-small-business",
                published_at=now - timedelta(days=5),
            ),
            KnowledgePage(
                brand_id=brand.id,
                title="Getting Started Guide",
                slug="getting-started-guide",
                status=PageStatus.DRAFT,
                mdx="# Getting Started with AcmeCRM\n\nQuick start guide...",
            ),
        ]

        for page in pages:
            db.add(page)

        print(f"Created {len(pages)} knowledge pages")

        db.commit()
        print("✅ Database seeded successfully!")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

