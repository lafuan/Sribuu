"""Tests untuk modul export CSV dan JSON."""


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

        # Verify header - updated columns per spec
        assert "Tanggal" in content
        assert "Deskripsi" in content
        assert "Jumlah" in content
        assert "Kategori" in content
        assert "Metode Pembayaran" in content
        assert "Catatan" in content
        assert "Tags" in content

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

    async def test_csv_with_tags(self, auth_client):
        """Export CSV harus mengekstrak tags dari notes."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 30000,
                "category_id": cat_id,
                "transaction_date": today,
                "notes": "Makan siang #makan #siang #kerja",
            },
        )

        response = await auth_client.get("/api/export/csv")
        assert response.status_code == 200
        content = response.text
        # Tags should be extracted
        assert "#makan" in content
        assert "#siang" in content
        assert "#kerja" in content

    async def test_csv_metadata_header(self, auth_client):
        """Export CSV harus menyertakan metadata di header komentar."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 25000,
                "category_id": cat_id,
                "transaction_date": today,
                "notes": "Test metadata",
            },
        )

        response = await auth_client.get("/api/export/csv")
        assert response.status_code == 200
        content = response.text
        # Check metadata in header
        assert "# Total Transaksi:" in content
        assert "# Tanggal Export:" in content
        assert "# Total Amount:" in content


class TestExportJSON:
    """Test GET /api/export/json"""

    async def test_json_empty(self, auth_client):
        """Export JSON tanpa data → 204 No Content."""
        response = await auth_client.get("/api/export/json")
        assert response.status_code == 204
        assert response.text == ""

    async def test_json_with_data(self, auth_client):
        """Export JSON dengan data → 200, ada konten JSON valid."""
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
                "notes": "Test JSON export",
            },
        )

        response = await auth_client.get("/api/export/json")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")

        import json
        data = json.loads(response.text)

        # Check structure
        assert "metadata" in data
        assert "transactions" in data
        assert len(data["transactions"]) == 1

        # Check transaction fields
        tx = data["transactions"][0]
        assert "date" in tx
        assert "description" in tx
        assert "amount" in tx
        assert "category" in tx
        assert "payment_method" in tx
        assert "notes" in tx
        assert "tags" in tx

        # Check metadata
        assert data["metadata"]["total_transactions"] == 1
        assert data["metadata"]["total_amount"] == 50000
        assert "export_date" in data["metadata"]

    async def test_json_with_tags(self, auth_client):
        """Export JSON harus mengekstrak tags dari notes."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={
                "amount": 30000,
                "category_id": cat_id,
                "transaction_date": today,
                "notes": "Makan siang #makan #siang",
            },
        )

        response = await auth_client.get("/api/export/json")
        assert response.status_code == 200

        import json
        data = json.loads(response.text)

        assert data["transactions"][0]["tags"] == ["makan", "siang"]

    async def test_json_content_disposition(self, auth_client):
        """Export JSON harus memiliki content-disposition dengan filename."""
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

        response = await auth_client.get("/api/export/json")
        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "")
        assert "pengeluaran_" in response.headers.get("content-disposition", "")
        assert ".json" in response.headers.get("content-disposition", "")
