"""Pytest configuration and fixtures for testing."""
import os
import sys
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, get_db
from app.main import app


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for the test
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def redis_client() -> Generator[Redis, None, None]:
    """Create a Redis client for testing (uses fakeredis if available)."""
    try:
        import fakeredis
        redis = fakeredis.FakeRedis(decode_responses=True)
    except ImportError:
        # Fall back to mock if fakeredis not available
        redis = MagicMock(spec=Redis)
        redis.exists.return_value = False
        redis.setex.return_value = True
        redis.expire.return_value = True
    
    yield redis
    
    # Cleanup
    if hasattr(redis, 'flushall'):
        redis.flushall()


@pytest.fixture
def auth_client(client: TestClient, db: Session):
    """
    Factory fixture for creating authenticated test clients.
    
    Usage:
        auth_client(user) -> TestClient with user authentication
    """
    def _auth_client(user):
        """Create an authenticated client for a specific user."""
        # Mock JWT verification to return the user
        with patch("app.auth.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {
                "sub": user.auth_provider_id,
                "email": user.email,
                "name": user.name,
            }
            
            # Create a copy of the client with auth headers
            auth_headers = {"Authorization": f"Bearer fake_token_{user.id}"}
            
            # Monkey-patch the client to always include auth headers
            original_request = client.request
            
            def authenticated_request(*args, **kwargs):
                if "headers" not in kwargs:
                    kwargs["headers"] = {}
                kwargs["headers"].update(auth_headers)
                return original_request(*args, **kwargs)
            
            client.request = authenticated_request
            
            return client
    
    return _auth_client


@pytest.fixture
def test_users(db: Session):
    """Create test users with different roles."""
    from app.models.user import User
    
    owner = User(auth_provider_id="owner_123", email="owner@test.com", name="Owner User")
    admin = User(auth_provider_id="admin_123", email="admin@test.com", name="Admin User")
    member = User(auth_provider_id="member_123", email="member@test.com", name="Member User")
    external = User(auth_provider_id="external_123", email="external@test.com", name="External User")
    
    db.add_all([owner, admin, member, external])
    db.commit()
    
    for user in [owner, admin, member, external]:
        db.refresh(user)
    
    return {
        "owner": owner,
        "admin": admin,
        "member": member,
        "external": external,
    }


@pytest.fixture
def mock_llm_providers():
    """Mock LLM provider responses."""
    with patch("app.llm_providers.openai_provider.OpenAIProvider.generate") as mock_openai, \
         patch("app.llm_providers.perplexity_provider.PerplexityProvider.generate") as mock_perplexity, \
         patch("app.llm_providers.google_provider.GoogleProvider.generate") as mock_google:
        
        # Mock successful LLM responses
        mock_response = MagicMock()
        mock_response.text = "Test response from LLM"
        mock_response.tokens_used = 100
        mock_response.finish_reason = "stop"
        
        mock_openai.return_value = mock_response
        mock_perplexity.return_value = mock_response
        mock_google.return_value = mock_response
        
        yield {
            "openai": mock_openai,
            "perplexity": mock_perplexity,
            "google": mock_google,
        }


@pytest.fixture
def disable_rate_limiting(monkeypatch):
    """Disable rate limiting for tests."""
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "False")


@pytest.fixture
def disable_auth(monkeypatch):
    """Disable auth requirement for tests (use with caution)."""
    monkeypatch.setenv("AUTH_REQUIRED", "False")
