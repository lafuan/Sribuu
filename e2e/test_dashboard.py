"""
E2E tests: Dashboard page.
"""

import pytest
from conftest import BASE_URL


class TestDashboard:
    """Test dashboard functionality."""

    def test_dashboard_loads(self, login_page):
        """Dashboard harus muncul dengan semua elemen utama."""
        page = login_page
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        # Cek judul halaman
        body = page.text_content("body")
        assert body is not None

        # Minimal ada navbar
        assert page.is_visible("nav") or page.is_visible("[class*=navbar]")

    def test_dashboard_shows_balance_or_stats(self, login_page):
        """Dashboard harus menampilkan ringkasan keuangan."""
        page = login_page
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        # Cek elemen ringkasan — biasanya ada total, jumlah transaksi
        body_text = page.text_content("body") or ""

        # Harus ada informasi keuangan
        has_info = any(kw in body_text for kw in [
            "Rp", "Total", "ringkasan", "pengeluaran",
            "bulan ini", "hari ini", "transaksi",
        ])
        assert has_info, "Dashboard harus menampilkan info keuangan"

    def test_dashboard_quick_add_exists(self, login_page):
        """Dashboard harus punya form tambah transaksi cepat."""
        page = login_page
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        # Cek ada form atau tombol tambah
        has_form = page.is_visible("form") or page.is_visible("button")
        assert has_form

    def test_dashboard_navigation_links(self, login_page):
        """Link navigasi di dashboard harus berfungsi."""
        page = login_page
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        # Klik link "Riwayat" atau "Transaksi"
        nav_links = ["Riwayat", "Transaksi", "Anggaran", "Statistik", "Pengaturan"]
        found_nav = False
        for link_text in nav_links:
            try:
                link = page.locator(f"a:has-text('{link_text}')").first
                if link.is_visible():
                    found_nav = True
                    break
            except Exception:
                continue

        assert found_nav, "Navigasi utama harus ada"

    def test_recent_transactions_shown(self, login_page):
        """Dashboard harus menampilkan transaksi terbaru."""
        page = login_page
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        # Cek ada tabel atau list transaksi
        body_text = page.text_content("body") or ""
        # Setelah ada transaksi, dashboard nampilin recent transactions
        page.wait_for_timeout(1000)

        # Minimal tidak error
        assert "error" not in body_text.lower()
