"""
E2E tests: Authentication flow — register, login, logout, validation.
"""

from conftest import BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD


class TestAuth:
    """Test authentication flows."""

    def test_login_page_loads(self, page):
        """Halaman login harus muncul dengan benar."""
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")
        assert "Login" in page.title()
        assert page.is_visible("input[name=email]")
        assert page.is_visible("input[name=password]")

    def test_login_success(self, page):
        """Login dengan kredensial valid harus redirect ke dashboard."""
        page.goto(f"{BASE_URL}/login")
        page.fill("input[name=email]", TEST_USER_EMAIL)
        page.fill("input[name=password]", TEST_USER_PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        # Should redirect to dashboard
        assert page.url.rstrip("/") == BASE_URL or page.url == f"{BASE_URL}/"

        # Dashboard harus menampilkan elemen kunci
        assert page.is_visible("text=Sribuu")

    def test_login_invalid_password(self, page):
        """Login dengan password salah harus menampilkan error."""
        page.goto(f"{BASE_URL}/login")
        page.fill("input[name=email]", TEST_USER_EMAIL)
        page.fill("input[name=password]", "wrongpassword123")
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        # Harus tetap di halaman login — dialog alert muncul
        # Karena JS pake alert(), Playwright otomatis dismiss
        # Cek URL masih /login
        assert "/login" in page.url

    def test_register_page_loads(self, page):
        """Halaman register harus muncul dengan benar."""
        page.goto(f"{BASE_URL}/register")
        page.wait_for_load_state("networkidle")
        assert "Register" in page.title() or "Create Account" in page.text_content("h1")
        assert page.is_visible("input[name=name]")
        assert page.is_visible("input[name=email]")
        assert page.is_visible("input[name=password]")
        assert page.is_visible("input[name=password_confirm]")

    def test_register_new_user(self, browser_context):
        """Registrasi user baru harus sukses."""
        import secrets
        unique = secrets.token_hex(4)
        page = browser_context.new_page()

        page.goto(f"{BASE_URL}/register")
        page.fill("input[name=name]", f"Test User {unique}")
        page.fill("input[name=email]", f"test_{unique}@test.com")
        page.fill("input[name=password]", "Test123456")
        page.fill("input[name=password_confirm]", "Test123456")
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        # Should redirect to dashboard
        assert page.url.rstrip("/") == BASE_URL or page.url == f"{BASE_URL}/"
        page.close()

    def test_register_password_mismatch(self, page):
        """Registrasi dengan konfirmasi password berbeda harus error."""
        import secrets
        unique = secrets.token_hex(4)

        page.goto(f"{BASE_URL}/register")
        page.fill("input[name=name]", f"Test {unique}")
        page.fill("input[name=email]", f"test_{unique}@test.com")
        page.fill("input[name=password]", "Test123456")
        page.fill("input[name=password_confirm]", "DifferentPass1")
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        # JS alert will fire, Playwright auto-dismisses
        # Should still be on /register
        assert "/register" in page.url

    def test_logout(self, login_page):
        """Logout harus redirect ke halaman login."""
        page = login_page

        # Click logout (cek di navbar)
        page.goto(f"{BASE_URL}/logout")
        page.wait_for_load_state("networkidle")

        # Should redirect to login page
        assert "/login" in page.url

    def test_authenticated_user_redirect_to_dashboard(self, login_page):
        """User yang sudah login harus di-redirect ke dashboard saat buka /login."""
        page = login_page

        # Buka /login dalam keadaan login
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")

        # Harus redirect ke /
        assert page.url.rstrip("/") == BASE_URL or page.url == f"{BASE_URL}/"
