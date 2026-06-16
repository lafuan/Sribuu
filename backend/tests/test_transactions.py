"""Tests untuk modul transaksi: CRUD, filter, pagination."""


class TestCreateTransaction:
    """Test POST /api/transactions"""

    async def test_create_valid(self, auth_client):
        """Buat transaksi valid → 201."""
        # Dapatkan kategori default (seeded)
        cat_resp = await auth_client.get("/api/categories")
        categories = cat_resp.json()["data"]["categories"]
        cat_id = categories[0]["id"]

        response = await auth_client.post(
            "/api/transactions",
            json={
                "amount": 50000,
                "category_id": cat_id,
                "transaction_date": "2026-06-15",
                "notes": "Makan siang",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["amount"] == 50000
        assert data["data"]["notes"] == "Makan siang"

    async def test_create_missing_fields(self, auth_client):
        """Buat transaksi tanpa amount → 422."""
        response = await auth_client.post(
            "/api/transactions",
            json={
                "category_id": 1,
            },
        )
        assert response.status_code == 422

    async def test_create_amount_zero(self, auth_client):
        """Buat transaksi dengan amount=0 → 422."""
        response = await auth_client.post(
            "/api/transactions",
            json={
                "amount": 0,
                "category_id": 1,
            },
        )
        assert response.status_code == 422

    async def test_create_amount_negative(self, auth_client):
        """Buat transaksi dengan amount negatif → 422."""
        response = await auth_client.post(
            "/api/transactions",
            json={
                "amount": -10000,
                "category_id": 1,
            },
        )
        assert response.status_code == 422

    async def test_create_nonexistent_category(self, auth_client):
        """Buat transaksi dengan category_id tidak ada → 422."""
        response = await auth_client.post(
            "/api/transactions",
            json={
                "amount": 50000,
                "category_id": 99999,
            },
        )
        assert response.status_code == 422


class TestListTransactions:
    """Test GET /api/transactions"""

    async def test_list_empty(self, auth_client):
        """List transaksi saat belum ada data."""
        response = await auth_client.get("/api/transactions")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["transactions"]) == 0
        assert data["data"]["summary"]["total_filtered"] == 0

    async def test_list_with_data(self, auth_client):
        """List setelah buat beberapa transaksi."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        # Buat 3 transaksi
        for i in range(3):
            await auth_client.post(
                "/api/transactions",
                json={
                    "amount": 10000 * (i + 1),
                    "category_id": cat_id,
                    "transaction_date": "2026-06-15",
                },
            )

        response = await auth_client.get("/api/transactions")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["transactions"]) == 3
        assert data["data"]["summary"]["total_filtered"] == 3

    async def test_pagination(self, auth_client):
        """Pagination: page & per_page berfungsi."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        # Buat 5 transaksi
        for i in range(5):
            await auth_client.post(
                "/api/transactions",
                json={
                    "amount": 10000 * (i + 1),
                    "category_id": cat_id,
                    "transaction_date": "2026-06-15",
                    "notes": f"Transaksi ke-{i + 1}",
                },
            )

        # Page 1, 2 per page
        resp = await auth_client.get("/api/transactions?page=1&per_page=2")
        data = resp.json()
        assert len(data["data"]["transactions"]) == 2
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["total_pages"] == 3
        assert data["data"]["pagination"]["has_next"] is True
        assert data["data"]["pagination"]["has_prev"] is False

        # Page 3
        resp = await auth_client.get("/api/transactions?page=3&per_page=2")
        data = resp.json()
        assert len(data["data"]["transactions"]) == 1
        assert data["data"]["pagination"]["has_next"] is False


class TestFilterTransactions:
    """Test filter pada GET /api/transactions"""

    async def test_filter_date_range(self, auth_client):
        """Filter berdasarkan rentang tanggal."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        await auth_client.post(
            "/api/transactions",
            json={"amount": 10000, "category_id": cat_id, "transaction_date": "2026-06-01"},
        )
        await auth_client.post(
            "/api/transactions",
            json={"amount": 20000, "category_id": cat_id, "transaction_date": "2026-06-20"},
        )

        resp = await auth_client.get("/api/transactions?date_from=2026-06-01&date_to=2026-06-10")
        data = resp.json()
        assert data["data"]["summary"]["total_filtered"] == 1

    async def test_filter_category(self, auth_client):
        """Filter berdasarkan kategori."""
        cat_resp = await auth_client.get("/api/categories")
        cats = cat_resp.json()["data"]["categories"]

        await auth_client.post(
            "/api/transactions",
            json={"amount": 10000, "category_id": cats[0]["id"], "transaction_date": "2026-06-15"},
        )
        await auth_client.post(
            "/api/transactions",
            json={"amount": 20000, "category_id": cats[1]["id"], "transaction_date": "2026-06-15"},
        )

        resp = await auth_client.get(f"/api/transactions?category_id={cats[0]['id']}")
        data = resp.json()
        assert data["data"]["summary"]["total_filtered"] == 1
        assert data["data"]["transactions"][0]["category"]["id"] == cats[0]["id"]

    async def test_filter_search_notes(self, auth_client):
        """Filter pencarian notes."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        await auth_client.post(
            "/api/transactions",
            json={"amount": 10000, "category_id": cat_id, "transaction_date": "2026-06-15",
                  "notes": "Beli kopi di starbucks"},
        )
        await auth_client.post(
            "/api/transactions",
            json={"amount": 20000, "category_id": cat_id, "transaction_date": "2026-06-15",
                  "notes": "Beli nasi goreng"},
        )

        resp = await auth_client.get("/api/transactions?search=kopi")
        data = resp.json()
        assert data["data"]["summary"]["total_filtered"] == 1

        resp = await auth_client.get("/api/transactions?search=tidakada")
        data = resp.json()
        assert data["data"]["summary"]["total_filtered"] == 0


class TestGetTransaction:
    """Test GET /api/transactions/{id}"""

    async def test_get_by_id_valid(self, auth_client):
        """Dapatkan transaksi by ID yang valid."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        create_resp = await auth_client.post(
            "/api/transactions",
            json={"amount": 75000, "category_id": cat_id, "transaction_date": "2026-06-15",
                  "notes": "Test detail"},
        )
        tx_id = create_resp.json()["data"]["id"]

        resp = await auth_client.get(f"/api/transactions/{tx_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["id"] == tx_id
        assert data["data"]["amount"] == 75000
        assert data["data"]["notes"] == "Test detail"

    async def test_get_by_id_nonexistent(self, auth_client):
        """Transaksi tidak ditemukan → 404."""
        resp = await auth_client.get("/api/transactions/99999")
        assert resp.status_code == 404


class TestUpdateTransaction:
    """Test PUT /api/transactions/{id}"""

    async def test_update_valid(self, auth_client):
        """Update transaksi valid."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        create_resp = await auth_client.post(
            "/api/transactions",
            json={"amount": 50000, "category_id": cat_id, "transaction_date": "2026-06-15"},
        )
        tx_id = create_resp.json()["data"]["id"]

        resp = await auth_client.put(
            f"/api/transactions/{tx_id}",
            json={"amount": 99999, "category_id": cat_id, "transaction_date": "2026-06-15",
                  "notes": "Updated!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["amount"] == 99999
        assert data["data"]["notes"] == "Updated!"

    async def test_update_nonexistent(self, auth_client):
        """Update transaksi tidak ada → 404."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        resp = await auth_client.put(
            "/api/transactions/99999",
            json={"amount": 10000, "category_id": cat_id, "transaction_date": "2026-06-15"},
        )
        assert resp.status_code == 404


class TestDeleteTransaction:
    """Test DELETE /api/transactions/{id}"""

    async def test_delete_valid(self, auth_client):
        """Hapus transaksi valid → 200, lalu 404 saat get ulang."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        create_resp = await auth_client.post(
            "/api/transactions",
            json={"amount": 50000, "category_id": cat_id, "transaction_date": "2026-06-15"},
        )
        tx_id = create_resp.json()["data"]["id"]

        resp = await auth_client.delete(f"/api/transactions/{tx_id}")
        assert resp.status_code == 200

        # Pastikan sudah terhapus
        resp = await auth_client.get(f"/api/transactions/{tx_id}")
        assert resp.status_code == 404

    async def test_delete_nonexistent(self, auth_client):
        """Hapus transaksi tidak ada → 404."""
        resp = await auth_client.delete("/api/transactions/99999")
        assert resp.status_code == 404
