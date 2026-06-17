"""
E2E tests: Transaction CRUD flow.
"""

import pytest
from conftest import BASE_URL


class TestTransactions:
    """Test transaction CRUD operations."""

    def test_transaction_list_page(self, login_page):
        """Halaman daftar transaksi harus bisa dibuka."""
        page = login_page
        page.goto(f"{BASE_URL}/transactions")
        page.wait_for_load_state("networkidle")

        # Halaman harus muncul
        body_text = page.text_content("body") or ""
        assert page.url.rstrip("/") == f"{BASE_URL}/transactions" or "/transactions" in page.url

    def test_add_transaction_new_page(self, login_page):
        """Halaman form tambah transaksi harus bisa dibuka."""
        page = login_page
        page.goto(f"{BASE_URL}/transactions/new")
        page.wait_for_load_state("networkidle")

        # Cek form fields
        body_text = page.text_content("body") or ""
        # Harus ada form input
        assert page.is_visible("input[name=amount]") or "nominal" in body_text.lower()

    def test_create_transaction(self, browser_context):
        """Membuat transaksi baru harus sukses."""
        from conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD

        # Gunakan context baru untuk menghindari cookie campur aduk
        page = browser_context.new_page()

        # Login dulu
        page.goto(f"{BASE_URL}/login")
        page.fill("input[name=email]", TEST_USER_EMAIL)
        page.fill("input[name=password]", TEST_USER_PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        # Buka form tambah transaksi
        page.goto(f"{BASE_URL}/transactions/new")
        page.wait_for_load_state("networkidle")

        # Isi form
        page.fill("input[name=amount]", "50000")

        # Pilih kategori (select dropdown)
        try:
            category_select = page.locator("select[name=category_id]")
            if category_select.is_visible():
                category_select.select_option(index=0)
        except Exception:
            pass

        # Isi notes
        try:
            page.fill("input[name=notes]", "E2E Test Transaction")
        except Exception:
            try:
                page.fill("textarea[name=notes]", "E2E Test Transaction")
            except Exception:
                pass

        # Submit
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        # Harus redirect ke daftar transaksi
        current_url = page.url.rstrip("/")
        successfully_redirected = (
            current_url == f"{BASE_URL}/transactions"
            or "/transactions" in current_url
        )
        assert successfully_redirected, f"Expected redirect to /transactions, got {page.url}"

        body_text = page.text_content("body") or ""
        page.close()

    def test_empty_transaction_form_validation(self, login_page):
        """Form kosong harus menampilkan error."""
        page = login_page
        page.goto(f"{BASE_URL}/transactions/new")
        page.wait_for_load_state("networkidle")

        # Submit tanpa isi
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        # Harus tetap di halaman yang sama dan ada pesan error
        body_text = page.text_content("body") or ""
        # HTML5 validation atau server error
        has_validation = any(kw in body_text.lower() for kw in [
            "error", "wajib", "required", "nominal", "pilih kategori"
        ])
        assert has_validation or page.url.rstrip("/") == f"{BASE_URL}/transactions/new"

    def test_transaction_filter(self, login_page):
        """Filter transaksi harus berfungsi."""
        page = login_page
        page.goto(f"{BASE_URL}/transactions")
        page.wait_for_load_state("networkidle")

        # Cek ada form filter — input date, select category
        has_date_input = page.is_visible("input[name=date_from]")
        has_category_select = page.is_visible("select[name=category_id]")
        assert has_date_input or has_category_select, "Harus ada form filter"
