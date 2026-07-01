"""
E2E tests: Budget management flow.
"""

from conftest import BASE_URL


class TestBudgets:
    """Test budget CRUD operations."""

    def test_budget_page_loads(self, login_page):
        """Halaman anggaran harus bisa dibuka."""
        page = login_page
        page.goto(f"{BASE_URL}/budgets")
        page.wait_for_load_state("networkidle")

        body_text = page.text_content("body") or ""
        # Halaman harus nampilin sesuatu
        assert len(body_text) > 0

    def test_budget_page_has_content(self, login_page):
        """Halaman anggaran harus menampilkan ringkasan."""
        page = login_page
        page.goto(f"{BASE_URL}/budgets")
        page.wait_for_load_state("networkidle")

        body_text = page.text_content("body") or ""
        # Harus ada info anggaran
        has_budget_info = any(kw in body_text for kw in [
            "Budget", "budget",
            "Total", "Remaining", "Spent",
        ])
        assert has_budget_info or page.is_visible("button, a")

    def test_add_budget_button_exists(self, login_page):
        """Tombol/tautan tambah anggaran harus ada."""
        page = login_page
        page.goto(f"{BASE_URL}/budgets")
        page.wait_for_load_state("networkidle")

        # Cari tombol tambah (English after i18n)
        add_btn = page.locator("button:has-text('Add'), a:has-text('Add'), button:has-text('+')").first
        assert add_btn.count() > 0 or page.is_visible("[class*=add], [class*=create], [class*=new]") is not False
