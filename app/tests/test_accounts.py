import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestUserRegistration:
    """Test user registration endpoint"""

    async def test_register_user_success(
        self, client: AsyncClient, user_groups, mocker
    ):
        """Test successful user registration"""
        mocker.patch("app.tasks.email_tasks.send_activation_email_task.delay")
        response = await client.post(
            "/api/v1/accounts/register/",
            json={
                "email": "newuser@example.com",
                "password": "NewUser123!",
                "first_name": "New",
                "last_name": "User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email"""
        response = await client.post(
            "/api/v1/accounts/register/",
            json={
                "email": "test@example.com",
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_register_weak_password(self, client: AsyncClient, user_groups):
        """Test registration with weak password"""
        response = await client.post(
            "/api/v1/accounts/register/",
            json={
                "email": "weak@example.com",
                "password": "weak",
            },
        )
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint"""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login"""
        response = await client.post(
            "/api/v1/accounts/login/",
            json={
                "email": "test@example.com",
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password"""
        response = await client.post(
            "/api/v1/accounts/login/",
            json={
                "email": "test@example.com",
                "password": "WrongPass123!",
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user"""
        response = await client.post(
            "/api/v1/accounts/login/",
            json={
                "email": "nonexistent@example.com",
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 401


class TestTokenRefresh:
    """Test token refresh endpoint"""

    async def test_refresh_token_success(self, client: AsyncClient, test_user):
        """Test successful token refresh"""
        # First login
        login_response = await client.post(
            "/api/v1/accounts/login/",
            json={
                "email": "test@example.com",
                "password": "TestPass123!",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/accounts/refresh/",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token"""
        response = await client.post(
            "/api/v1/accounts/refresh/",
            json={"refresh_token": "invalid_token"},
        )
        assert response.status_code == 401


class TestPasswordReset:
    """Test password reset endpoints"""

    async def test_request_password_reset(self, client: AsyncClient, test_user, mocker):
        """Test password reset request"""
        mocker.patch("app.tasks.email_tasks.send_password_reset_email_task.delay")
        response = await client.post(
            "/api/v1/accounts/password-reset/request/",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 200
        assert "message" in response.json()

    async def test_request_password_reset_nonexistent(self, client: AsyncClient):
        """Test password reset for non-existent user"""
        response = await client.post(
            "/api/v1/accounts/password-reset/request/",
            json={"email": "nonexistent@example.com"},
        )
        # Should return 200 for security (don't reveal user existence)
        assert response.status_code == 200
