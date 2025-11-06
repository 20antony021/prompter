"""Tests for authentication and role-based access control."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.brand import Brand
from app.models.org import Org, OrgMember, OrgRole
from app.models.user import User


@pytest.fixture
def test_org(db: Session):
    """Create test organization."""
    org = Org(name="Test Org", slug="test-org", plan_tier="growth")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def test_users(db: Session):
    """Create test users with different roles."""
    owner = User(auth_provider_id="owner_123", email="owner@test.com", name="Owner User")
    admin = User(auth_provider_id="admin_123", email="admin@test.com", name="Admin User")
    member = User(auth_provider_id="member_123", email="member@test.com", name="Member User")
    external = User(auth_provider_id="external_123", email="external@test.com", name="External User")
    
    db.add_all([owner, admin, member, external])
    db.commit()
    
    return {
        "owner": owner,
        "admin": admin,
        "member": member,
        "external": external,
    }


@pytest.fixture
def test_org_members(db: Session, test_org, test_users):
    """Create org memberships with different roles."""
    owner_member = OrgMember(org_id=test_org.id, user_id=test_users["owner"].id, role=OrgRole.OWNER)
    admin_member = OrgMember(org_id=test_org.id, user_id=test_users["admin"].id, role=OrgRole.ADMIN)
    basic_member = OrgMember(org_id=test_org.id, user_id=test_users["member"].id, role=OrgRole.MEMBER)
    
    db.add_all([owner_member, admin_member, basic_member])
    db.commit()
    
    return {
        "owner": owner_member,
        "admin": admin_member,
        "member": basic_member,
    }


@pytest.fixture
def test_brand(db: Session, test_org):
    """Create test brand."""
    brand = Brand(
        org_id=test_org.id,
        name="Test Brand",
        website="https://example.com",
        primary_domain="example.com",
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


class TestAuthenticationRequired:
    """Test that authentication is required for all endpoints."""

    def test_list_brands_requires_auth(self, client: TestClient, test_org):
        """Listing brands should require authentication."""
        response = client.get(f"/v1/brands?org_id={test_org.id}")
        assert response.status_code == 401
        assert "unauthorized" in response.json()["error"]["code"].lower()

    def test_create_brand_requires_auth(self, client: TestClient, test_org):
        """Creating a brand should require authentication."""
        response = client.post(
            "/v1/brands",
            json={
                "org_id": test_org.id,
                "name": "New Brand",
                "website": "https://newbrand.com",
            },
        )
        assert response.status_code == 401

    def test_update_brand_requires_auth(self, client: TestClient, test_brand):
        """Updating a brand should require authentication."""
        response = client.put(
            f"/v1/brands/{test_brand.id}",
            json={"name": "Updated Brand"},
        )
        assert response.status_code == 401


class TestRoleBasedAccessControl:
    """Test role-based access control."""

    def test_member_cannot_create_brand(
        self, auth_client, test_org, test_users, test_org_members
    ):
        """Members should not be able to create brands (admin/owner only)."""
        client = auth_client(test_users["member"])
        response = client.post(
            "/v1/brands",
            json={
                "org_id": test_org.id,
                "name": "New Brand",
                "website": "https://newbrand.com",
            },
        )
        assert response.status_code == 403
        assert "forbidden" in response.json()["error"]["code"].lower()

    def test_admin_can_create_brand(
        self, auth_client, test_org, test_users, test_org_members
    ):
        """Admins should be able to create brands."""
        client = auth_client(test_users["admin"])
        response = client.post(
            "/v1/brands",
            json={
                "org_id": test_org.id,
                "name": "Admin Brand",
                "website": "https://adminbrand.com",
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Admin Brand"

    def test_owner_can_create_brand(
        self, auth_client, test_org, test_users, test_org_members
    ):
        """Owners should be able to create brands."""
        client = auth_client(test_users["owner"])
        response = client.post(
            "/v1/brands",
            json={
                "org_id": test_org.id,
                "name": "Owner Brand",
                "website": "https://ownerbrand.com",
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Owner Brand"

    def test_member_can_view_brands(
        self, auth_client, test_org, test_brand, test_users, test_org_members
    ):
        """Members should be able to view brands in their org."""
        client = auth_client(test_users["member"])
        response = client.get(f"/v1/brands?org_id={test_org.id}")
        assert response.status_code == 200
        brands = response.json()["items"]
        assert len(brands) > 0

    def test_external_user_cannot_view_brands(
        self, auth_client, test_org, test_brand, test_users
    ):
        """Users not in org should not be able to view org brands."""
        client = auth_client(test_users["external"])
        response = client.get(f"/v1/brands?org_id={test_org.id}")
        assert response.status_code == 403
        assert "not authorized" in response.json()["error"]["message"].lower()


class TestMultiTenantIsolation:
    """Test that users can only access data from their own organization."""

    def test_cannot_access_other_org_brands(
        self, auth_client, db, test_org, test_brand, test_users, test_org_members
    ):
        """Users should not be able to access brands from other organizations."""
        # Create another org and brand
        other_org = Org(name="Other Org", slug="other-org", plan_tier="starter")
        db.add(other_org)
        db.commit()
        
        other_brand = Brand(
            org_id=other_org.id,
            name="Other Brand",
            website="https://otherbrand.com",
        )
        db.add(other_brand)
        db.commit()

        # Try to access other org's brands
        client = auth_client(test_users["owner"])
        response = client.get(f"/v1/brands?org_id={other_org.id}")
        assert response.status_code == 403

    def test_cannot_update_other_org_brands(
        self, auth_client, db, test_org, test_users, test_org_members
    ):
        """Users should not be able to update brands from other organizations."""
        # Create another org and brand
        other_org = Org(name="Other Org", slug="other-org", plan_tier="starter")
        db.add(other_org)
        db.commit()
        
        other_brand = Brand(
            org_id=other_org.id,
            name="Other Brand",
            website="https://otherbrand.com",
        )
        db.add(other_brand)
        db.commit()

        # Try to update other org's brand
        client = auth_client(test_users["owner"])
        response = client.put(
            f"/v1/brands/{other_brand.id}",
            json={"name": "Hacked Brand"},
        )
        assert response.status_code == 403


class TestAuditLogging:
    """Test that audit logs are created for sensitive operations."""

    def test_brand_creation_is_audited(
        self, auth_client, db, test_org, test_users, test_org_members
    ):
        """Brand creation should create an audit log entry."""
        from app.models.audit_log import AuditAction, AuditLog

        client = auth_client(test_users["admin"])
        
        # Count audit logs before
        before_count = db.query(AuditLog).count()
        
        # Create brand
        response = client.post(
            "/v1/brands",
            json={
                "org_id": test_org.id,
                "name": "Audited Brand",
                "website": "https://audited.com",
            },
        )
        assert response.status_code == 201
        brand_id = response.json()["id"]
        
        # Check audit log was created
        after_count = db.query(AuditLog).count()
        assert after_count == before_count + 1
        
        # Verify audit log details
        audit_log = db.query(AuditLog).filter(
            AuditLog.resource_type == "brand",
            AuditLog.resource_id == brand_id,
        ).first()
        
        assert audit_log is not None
        assert audit_log.action == AuditAction.CREATE
        assert audit_log.user_id == test_users["admin"].id
        assert audit_log.org_id == test_org.id

    def test_brand_update_is_audited(
        self, auth_client, db, test_org, test_brand, test_users, test_org_members
    ):
        """Brand updates should create audit log entries with change details."""
        from app.models.audit_log import AuditAction, AuditLog

        client = auth_client(test_users["admin"])
        
        # Update brand
        response = client.put(
            f"/v1/brands/{test_brand.id}",
            json={"name": "Updated Brand Name"},
        )
        assert response.status_code == 200
        
        # Verify audit log
        audit_log = db.query(AuditLog).filter(
            AuditLog.action == AuditAction.UPDATE,
            AuditLog.resource_type == "brand",
            AuditLog.resource_id == test_brand.id,
        ).first()
        
        assert audit_log is not None
        assert "changes" in audit_log.details
        assert "name" in audit_log.details["changes"]
        assert audit_log.details["changes"]["name"]["new"] == "Updated Brand Name"

