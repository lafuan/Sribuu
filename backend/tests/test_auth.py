"""Tests untuk modul autentikasi: register, login, logout, me, password."""
import pytest
from unittest.mock import MagicMock


class TestCookieSecurity:
    """Test that the access_token cookie security is set correctly."""

    @pytest.mark.parametrize(
        "debug_mode, expected_secure_flag",
        [
            (True, False),  # In debug mode, cookie should NOT be secure
            (False, True),  # In production (not debug), cookie MUST be secure
        ],
    )
    async def test_cookie_security_on_login(
        self, client, test_user, monkeypatch, debug_mode, expected_secure_flag
    ):
        """Verify 'secure' flag on login based on DEBUG setting."""
        # Create a mock settings object
        mock_settings = MagicMock()
        mock_settings.DEBUG = debug_mode

        # Patch the settings object within the auth_service module's namespace
        monkeypatch.setattr("backend.services.auth_service.settings", mock_settings)

        response = await client.post(
            "/api/auth/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )

        assert response.status_code == 200
        cookie_header = response.headers["set-cookie"]
        assert "access_token=" in cookie_header

        # Check for the 'Secure' flag in the cookie string.
        has_secure_flag = "Secure" in [p.strip() for p in cookie_header.split(";")]
        assert has_secure_flag is expected_secure_flag


class TestRegister:
    """Test endpoint POST /api/auth/register"""

    async def test_register_valid(self, client):
        """Registrasi dengan data valid menghasilkan 201."""
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "Alice",
                "email": "alice@example.com",
                "password": "secure123",
                "password_confirm": "secure123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["user"]["email"] == "alice@example.com"
        assert data["data"]["user"]["name"] == "Alice"
        assert "access_token" in response.cookies

    async def test_register_duplicate_email(self, client, test_user):
        """Registrasi dengan email yang sudah terdaftar → 409."""
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "Duplicate",
                "email": test_user["email"],
                "password": "secure123",
                "password_confirm": "secure123",
            },
        )
        assert response.status_code == 409
        data = response.json()
        # FastAPI wraps HTTPException detail in {"detail": {...}}
        assert "detail" in data
        assert data["detail"]["status"] == "error"

    async def test_register_invalid_email(self, client):
        """Registrasi dengan email tidak valid → 422."""
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "Bob",
                "email": "not-an-email",
                "password": "secure123",
                "password_confirm": "secure123",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client):
        """Registrasi dengan password < 6 karakter → 422."""
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "Charlie",
                "email": "charlie@example.com",
                "password": "ab",
                "password_confirm": "ab",
            },
        )
        assert response.status_code == 422

    async def test_register_password_mismatch(self, client):
        """Password dan konfirmasi tidak cocok → 422."""
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "Diana",
                "email": "diana@example.com",
                "password": "secure123",
                "password_confirm": "different",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Test endpoint POST /api/auth/login"""

    async def test_login_valid(self, client, test_user):
        """Login dengan kredensial valid → 200."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["user"]["email"] == test_user["email"]
        assert "access_token" in response.cookies

    async def test_login_wrong_password(self, client, test_user):
        """Login dengan password salah → 401."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"]["status"] == "error"

    async def test_login_nonexistent_user(self, client):
        """Login dengan email tidak terdaftar → 401."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "ghost@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401


class TestLogout:
    """Test endpoint POST /api/auth/logout"""

    async def test_logout(self, client, test_user):
        """Logout → 200, cookie dihapus."""
        # Login dulu
        login_resp = await client.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        client.cookies = login_resp.cookies

        response = await client.post("/api/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Cookie harus di-clear (max-age=0 atau value kosong)
        cookie = response.cookies.get("access_token")
        assert cookie in {'""', "", None}


class TestGetMe:
    """Test endpoint GET /api/auth/me"""

    async def test_get_me_with_token(self, auth_client, test_user):
        """GET /me dengan token valid → 200."""
        response = await auth_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["user"]["email"] == test_user["email"]

    async def test_get_me_without_token(self, client):
        """GET /me tanpa token → 401."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401


class TestChangePassword:
    """Test endpoint PUT /api/auth/password"""

    async def test_change_password_valid(self, auth_client, test_user):
        """Ganti password dengan data valid → 200."""
        response = await auth_client.put(
            "/api/auth/password",
            json={
                "old_password": test_user["password"],
                "new_password": "newpass456",
                "new_password_confirm": "newpass456",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "success" in data["message"].lower()

    async def test_change_password_wrong_old(self, auth_client):
        """Ganti password dengan old_password salah → 400."""
        response = await auth_client.put(
            "/api/auth/password",
            json={
                "old_password": "wrongoldpassword",
                "new_password": "newpass456",
                "new_password_confirm": "newpass456",
            },
        )
        assert response.status_code == 400

    async def test_change_password_mismatch(self, auth_client, test_user):
        """Password baru dan konfirmasi tidak cocok → 422."""
        response = await auth_client.put(
            "/api/auth/password",
            json={
                "old_password": test_user["password"],
                "new_password": "newpass456",
                "new_password_confirm": "different",
            },
        )
        assert response.status_code == 422
