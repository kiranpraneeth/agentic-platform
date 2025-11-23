"""
Authentication Tests

Tests for user authentication, registration, and JWT token handling.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Tenant, User
from src.core.security import create_access_token, get_password_hash, verify_password


@pytest.mark.auth
@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hash_and_verify(self):
        """Test that password hashing and verification works."""
        password = "mysecurepassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.auth
@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test that access token is created."""
        data = {"sub": "user-id-123"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_subject(self):
        """Test that token contains the subject claim."""
        from jose import jwt

        from src.core.config import settings

        user_id = "user-id-456"
        token = create_access_token({"sub": user_id})
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])

        assert decoded["sub"] == user_id
        assert "exp" in decoded


@pytest.mark.auth
@pytest.mark.api
@pytest.mark.asyncio
class TestUserRegistration:
    """Test user registration endpoint."""

    async def test_register_new_user(
        self, client: AsyncClient, test_tenant: Tenant, db_session: AsyncSession
    ):
        """Test registering a new user."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepass123",
                "full_name": "New User",
                "tenant_slug": test_tenant.slug,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user: User, test_tenant: Tenant
    ):
        """Test that registering duplicate email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "different",
                "password": "pass123",
                "full_name": "Different User",
                "tenant_slug": test_tenant.slug,
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient, test_tenant: Tenant):
        """Test that invalid email is rejected."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "user",
                "password": "pass123",
                "full_name": "User",
                "tenant_slug": test_tenant.slug,
            },
        )

        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient, test_tenant: Tenant):
        """Test that weak password is rejected."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "123",  # Too short
                "full_name": "User",
                "tenant_slug": test_tenant.slug,
            },
        )

        assert response.status_code == 422


@pytest.mark.auth
@pytest.mark.api
@pytest.mark.asyncio
class TestUserLogin:
    """Test user login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password",
            },
        )

        assert response.status_code == 401

    async def test_login_inactive_user(
        self, client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """Test login with inactive user."""
        test_user.is_active = False
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123",
            },
        )

        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()


@pytest.mark.auth
@pytest.mark.api
@pytest.mark.asyncio
class TestAuthenticatedEndpoints:
    """Test accessing protected endpoints."""

    async def test_access_protected_endpoint_with_token(
        self, authenticated_client: AsyncClient
    ):
        """Test accessing protected endpoint with valid token."""
        response = await authenticated_client.get("/api/v1/agents")

        assert response.status_code == 200

    async def test_access_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/api/v1/agents")

        assert response.status_code == 401

    async def test_access_protected_endpoint_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        client.headers["Authorization"] = "Bearer invalid-token"
        response = await client.get("/api/v1/agents")

        assert response.status_code == 401

    async def test_access_protected_endpoint_expired_token(self, client: AsyncClient):
        """Test accessing protected endpoint with expired token."""
        from datetime import timedelta

        from src.core.security import create_access_token

        # Create token that expires immediately
        expired_token = create_access_token(
            {"sub": "user-id"}, expires_delta=timedelta(seconds=-1)
        )

        client.headers["Authorization"] = f"Bearer {expired_token}"
        response = await client.get("/api/v1/agents")

        assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.api
@pytest.mark.asyncio
class TestCurrentUser:
    """Test getting current user information."""

    async def test_get_current_user(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test getting current user info."""
        response = await authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert "hashed_password" not in data

    async def test_get_current_user_without_auth(self, client: AsyncClient):
        """Test that unauthorized request fails."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.asyncio
class TestMultiTenantAuth:
    """Test multi-tenant authentication isolation."""

    async def test_user_cannot_access_other_tenant_data(
        self,
        client: AsyncClient,
        test_user: User,
        tenant_factory,
        user_factory,
        agent_factory,
        db_session: AsyncSession,
    ):
        """Test that user can only access their tenant's data."""
        # Create another tenant with user and agent
        other_tenant = await tenant_factory(name="Other Tenant")
        other_user = await user_factory(other_tenant.id, "other@example.com")
        other_agent = await agent_factory(other_tenant.id, other_user.id, "Other Agent")

        # Create token for test_user
        token = create_access_token({"sub": str(test_user.id)})
        client.headers["Authorization"] = f"Bearer {token}"

        # Try to access other tenant's agent
        response = await client.get(f"/api/v1/agents/{other_agent.id}")

        assert response.status_code == 404  # Should not find agent from other tenant
