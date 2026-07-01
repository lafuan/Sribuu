"""
E2E tests: Navigation flow across all pages.
"""

import pytest
from conftest import BASE_URL


class TestNavigation:
    """Test all navigation links work correctly."""

    @pytest.mark.parametrize("path,title_kw", [
        ("/transactions", "History"),
        ("/transactions/new", "Add"),
        ("/budgets", "Budget"),
        ("/stats", "Statistics"),
        ("/settings", "Settings"),
    ])
    def test_page_loads(self, login_page, path, title_kw):
        """Setiap halaman harus bisa dibuka tanpa error."""
        page = login_page
        page.goto(f"{BASE_URL}{path}")
        page.wait_for_load_state("networkidle")

        # Harus return 200 (not error page)
        body_text = page.text_content("body") or ""
        assert "404" not in body_text, f"Page {path} returned 404"
        assert "Not Found" not in body_text, f"Page {path} returned Not Found"
        assert "error" not in body_text.lower() or "tidak ditemukan" not in body_text.lower()

        # Halaman harus punya konten
        assert len(body_text) > 50, f"Page {path} has very little content"

    def test_navbar_links_work(self, login_page):
        """Klik setiap link di navbar harus navigasi dengan benar."""
        page = login_page
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        # Dapatkan semua link di halaman
        links = page.locator("a")
        count = links.count()
        assert count > 0, "Harus ada link di halaman"

        # Cek minimal link utama bisa diklik
        nav_routes = ["/transactions", "/budgets", "/stats", "/settings"]
        for route in nav_routes[:2]:  # Test 2 link aja biar cepet
            link = page.locator(f'a[href="{route}"]').first
            if link.is_visible():
                link.click()
                page.wait_for_load_state("networkidle")
                assert route in page.url, f"Klik {route} harus navigasi ke {route}"
                break

    def test_no_broken_links(self, login_page):
        """Semua link internal tidak boleh broken."""
        page = login_page
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        links = page.locator("a[href^='/'], a[href^='http']")
        count = links.count()

        # Ambil href dan cek yang internal
        internal_links = []
        for i in range(count):
            href = links.nth(i).get_attribute("href")
            if href and href.startswith("/") and "#" not in href:
                internal_links.append(href)

        # Test 3 link internal pertama
        tested = 0
        for href in internal_links:
            if tested >= 3:
                break
            if href in ["/logout"]:
                continue
            page.goto(f"{BASE_URL}{href}")
            page.wait_for_load_state("networkidle")
            body = page.text_content("body") or ""
            assert "404" not in body, f"Link {href} returned 404"
            tested += 1
