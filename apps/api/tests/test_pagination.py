"""Tests for cursor-based pagination."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.org import Org, OrgMember, OrgRole
from app.models.user import User


@pytest.fixture
def test_org_with_brands(db: Session, auth_client, test_users):
    """Create an org with multiple brands for pagination testing."""
    org = Org(name="Test Org", slug="test-org", plan_tier="growth")
    db.add(org)
    db.commit()
    
    user = test_users["owner"]
    org_member = OrgMember(org_id=org.id, user_id=user.id, role=OrgRole.OWNER)
    db.add(org_member)
    db.commit()
    
    # Create 25 brands
    brands = []
    for i in range(25):
        brand = Brand(
            org_id=org.id,
            name=f"Brand {i:02d}",
            website=f"https://brand{i:02d}.com",
        )
        brands.append(brand)
    
    db.add_all(brands)
    db.commit()
    
    return {"org": org, "brands": brands, "user": user}


class TestCursorPagination:
    """Test cursor-based pagination implementation."""

    def test_pagination_default_limit(self, auth_client, test_org_with_brands):
        """Test that default limit is applied."""
        client = auth_client(test_org_with_brands["user"])
        org_id = test_org_with_brands["org"].id
        
        response = client.get(f"/v1/brands?org_id={org_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "next_cursor" in data
        assert "has_more" in data
        
        # Default limit is 50, we have 25 brands
        assert len(data["items"]) == 25
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    def test_pagination_custom_limit(self, auth_client, test_org_with_brands):
        """Test pagination with custom limit."""
        client = auth_client(test_org_with_brands["user"])
        org_id = test_org_with_brands["org"].id
        
        response = client.get(f"/v1/brands?org_id={org_id}&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 10
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

    def test_pagination_multiple_pages(self, auth_client, test_org_with_brands):
        """Test fetching multiple pages."""
        client = auth_client(test_org_with_brands["user"])
        org_id = test_org_with_brands["org"].id
        
        # First page
        response = client.get(f"/v1/brands?org_id={org_id}&limit=10")
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1["items"]) == 10
        assert page1["has_more"] is True
        
        # Second page
        cursor = page1["next_cursor"]
        response = client.get(f"/v1/brands?org_id={org_id}&limit=10&cursor={cursor}")
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2["items"]) == 10
        assert page2["has_more"] is True
        
        # Third page
        cursor = page2["next_cursor"]
        response = client.get(f"/v1/brands?org_id={org_id}&limit=10&cursor={cursor}")
        assert response.status_code == 200
        page3 = response.json()
        assert len(page3["items"]) == 5  # Remaining brands
        assert page3["has_more"] is False
        assert page3["next_cursor"] is None
        
        # Verify no duplicates across pages
        all_ids = set()
        for page in [page1, page2, page3]:
            page_ids = {item["id"] for item in page["items"]}
            assert len(all_ids & page_ids) == 0  # No overlap
            all_ids.update(page_ids)
        
        assert len(all_ids) == 25  # All brands accounted for

    def test_pagination_invalid_cursor(self, auth_client, test_org_with_brands):
        """Test that invalid cursors are handled gracefully."""
        client = auth_client(test_org_with_brands["user"])
        org_id = test_org_with_brands["org"].id
        
        response = client.get(f"/v1/brands?org_id={org_id}&cursor=invalid")
        assert response.status_code == 422  # Validation error

    def test_pagination_limit_bounds(self, auth_client, test_org_with_brands):
        """Test pagination limit validation."""
        client = auth_client(test_org_with_brands["user"])
        org_id = test_org_with_brands["org"].id
        
        # Too small
        response = client.get(f"/v1/brands?org_id={org_id}&limit=0")
        assert response.status_code == 422
        
        # Too large
        response = client.get(f"/v1/brands?org_id={org_id}&limit=101")
        assert response.status_code == 422
        
        # Valid bounds
        response = client.get(f"/v1/brands?org_id={org_id}&limit=1")
        assert response.status_code == 200
        
        response = client.get(f"/v1/brands?org_id={org_id}&limit=100")
        assert response.status_code == 200

