"""Tests untuk modul export CSV."""
import pytest


class TestExportCSV:
    """Test GET /api/export/csv"""

    async def test_csv_empty(self, auth_client):
        """Export CSV tanpa data → 204 No Content."""
        response = await auth_client.get("/api/export/csv")
        assert response.status_code == 204
        assert response.text == ""

    async def test_csv_with_data(self, auth_client):
        """Export CSV dengan data → 200, ada konten CSV."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 50000,
                "category_id": cat_id,
                "transaction_date": today,
                "notes": "Test export",
            },
        )

        response = await auth_client.get("/api/export/csv")
        assert response.status_code == 200
        content = response.text

        # Verify header
        assert "Tanggal" in content
        assert "Kategori" in content
        assert "Jumlah" in content
        assert "Metode Pembayaran" in content
        assert "Catatan" in content

        # Verify data
        assert "Test export" in content
        assert "50000" in content

    async def test_csv_utf8_bom(self, auth_client):
        """Export CSV harus dimulai dengan BOM UTF-8 (\\ufeff)."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 10000,
                "category_id": cat_id,
                "transaction_date": today,
                "notes": "BOM test",
            },
        )

        response = await auth_client.get("/api/export/csv")
        assert response.status_code == 200
        content = response.text
        # Check BOM
        assert content.startswith("\ufeff")

    async def test_csv_content_type(self, auth_client):
        """Export CSV harus memiliki content-type text/csv."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 10000,
                "category_id": cat_id,
                "transaction_date": today,
            },
        )

        response = await auth_client.get("/api/export/csv")
        assert "text/csv" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")
