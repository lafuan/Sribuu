"""Tests untuk modul laporan PDF bulanan."""


class TestMonthlyReport:
    """Test GET /api/reports/monthly"""

    async def test_report_no_data(self, auth_client):
        """Download PDF tanpa data transaksi -> tetap return 200 (PDF kosong)."""
        response = await auth_client.get("/api/reports/monthly")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")

    async def test_report_with_data(self, auth_client):
        """Download PDF dengan data transaksi -> PDF valid."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date

        today = date.today().isoformat()

        # Add some transactions
        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 50000,
                "category_id": cat_id,
                "transaction_date": today,
                "notes": "Test PDF report",
            },
        )
        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 25000,
                "category_id": cat_id,
                "transaction_date": today,
                "notes": "Test PDF report 2",
            },
        )

        response = await auth_client.get("/api/reports/monthly")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")

        # Verify it's a valid PDF (starts with %PDF)
        content = response.content
        assert content[:4] == b"%PDF"

    async def test_report_specific_month(self, auth_client):
        """Download PDF untuk bulan spesifik."""
        response = await auth_client.get("/api/reports/monthly?year=2026&month=1")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"

    async def test_report_content_disposition_filename(self, auth_client):
        """Filename response harus berformat laporan_sribuu_YYYY_MM.pdf."""
        response = await auth_client.get("/api/reports/monthly?year=2026&month=6")
        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        assert "laporan_sribuu_2026_06.pdf" in disposition

    async def test_report_unauthenticated(self, client):
        """Download PDF tanpa auth -> 401."""
        response = await client.get("/api/reports/monthly")
        assert response.status_code == 401

    async def test_report_invalid_month(self, auth_client):
        """Bulan invalid -> 422."""
        response = await auth_client.get("/api/reports/monthly?month=13")
        assert response.status_code == 422

    async def test_report_with_budget_data(self, auth_client):
        """Download PDF dengan budget data -> tetap return 200."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date

        today = date.today()

        # Create budget
        await auth_client.post(
            "/api/budgets",
            json={
                "category_id": cat_id,
                "month": today.month,
                "year": today.year,
                "amount": 1000000,
            },
        )

        # Add transaction in budget category
        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 300000,
                "category_id": cat_id,
                "transaction_date": today.isoformat(),
                "notes": "Budget test",
            },
        )

        response = await auth_client.get("/api/reports/monthly")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content[:4] == b"%PDF"
