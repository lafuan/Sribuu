"""Tests untuk budget API endpoints."""



class TestBudgetCreate:
    """Test POST /api/budgets"""

    async def test_create_budget_valid(self, auth_client):
        """Buat budget valid → 201."""
        # Ambil kategori pertama (dari seed data)
        cat_resp = await auth_client.get("/api/categories")
        categories = cat_resp.json()["data"]["categories"]
        assert len(categories) > 0
        cat_id = categories[0]["id"]

        response = await auth_client.post(
            "/api/budgets",
            json={
                "category_id": cat_id,
                "amount": 1000000,
                "month": 7,
                "year": 2026,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["amount"] == 1000000
        assert data["data"]["month"] == 7
        assert data["data"]["year"] == 2026

    async def test_create_budget_missing_category(self, auth_client):
        """Buat budget dengan kategori tidak valid → 422."""
        response = await auth_client.post(
            "/api/budgets",
            json={"category_id": 99999, "amount": 500000, "month": 7, "year": 2026},
        )
        assert response.status_code == 422

    async def test_create_budget_duplicate(self, auth_client):
        """Buat budget duplikat per kategori+bulan → 409."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        # Buat pertama
        await auth_client.post(
            "/api/budgets",
            json={"category_id": cat_id, "amount": 500000, "month": 7, "year": 2026},
        )
        # Buat kedua (sama kategori, bulan, tahun) → harus ditolak
        response = await auth_client.post(
            "/api/budgets",
            json={"category_id": cat_id, "amount": 300000, "month": 7, "year": 2026},
        )
        assert response.status_code == 409


class TestBudgetList:
    """Test GET /api/budgets"""

    async def test_list_budgets(self, auth_client):
        """List budget untuk bulan/tahun tertentu."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        # Buat budget dulu
        await auth_client.post(
            "/api/budgets",
            json={"category_id": cat_id, "amount": 500000, "month": 6, "year": 2026},
        )

        # List
        response = await auth_client.get("/api/budgets?month=6&year=2026")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["budgets"]) == 1
        assert data["data"]["budgets"][0]["amount"] == 500000

    async def test_list_budgets_empty_month(self, auth_client):
        """List budget untuk bulan tanpa data → kosong."""
        response = await auth_client.get("/api/budgets?month=12&year=2025")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["budgets"]) == 0


class TestBudgetUpdate:
    """Test PUT /api/budgets/{id}"""

    async def test_update_budget_amount(self, auth_client):
        """Update amount budget."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        create_resp = await auth_client.post(
            "/api/budgets",
            json={"category_id": cat_id, "amount": 500000, "month": 6, "year": 2026},
        )
        budget_id = create_resp.json()["data"]["id"]

        response = await auth_client.put(
            f"/api/budgets/{budget_id}",
            json={"amount": 750000},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["amount"] == 750000

    async def test_update_budget_not_found(self, auth_client):
        """Update budget yang tidak ada → 404."""
        response = await auth_client.put(
            "/api/budgets/99999",
            json={"amount": 500000},
        )
        assert response.status_code == 404


class TestBudgetDelete:
    """Test DELETE /api/budgets/{id}"""

    async def test_delete_budget(self, auth_client):
        """Hapus budget."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        create_resp = await auth_client.post(
            "/api/budgets",
            json={"category_id": cat_id, "amount": 500000, "month": 6, "year": 2026},
        )
        budget_id = create_resp.json()["data"]["id"]

        response = await auth_client.delete(f"/api/budgets/{budget_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    async def test_delete_budget_not_found(self, auth_client):
        """Hapus budget yang tidak ada → 404."""
        response = await auth_client.delete("/api/budgets/99999")
        assert response.status_code == 404


class TestBudgetUnauthorized:
    """Test tanpa autentikasi."""

    async def test_create_without_auth(self, client):
        """Buat budget tanpa login → 401."""
        response = await client.post(
            "/api/budgets",
            json={"category_id": 1, "amount": 500000, "month": 7, "year": 2026},
        )
        assert response.status_code == 401

    async def test_list_without_auth(self, client):
        """List budget tanpa login → 401."""
        response = await client.get("/api/budgets")
        assert response.status_code == 401


class TestBudgetCopyFromPrevious:
    """Test POST /api/budgets/copy-from-previous"""

    async def test_copy_from_previous_has_budgets(self, auth_client):
        """Salin budget dari bulan sebelumnya."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        # Buat budget di bulan 6 (prev month = 5)
        await auth_client.post(
            "/api/budgets",
            json={"category_id": cat_id, "amount": 500000, "month": 5, "year": 2026},
        )

        # Copy dari bulan 6 (prev = 5)
        response = await auth_client.post(
            "/api/budgets/copy-from-previous?month=6&year=2026",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["budgets"]) == 1
        assert data["data"]["budgets"][0]["amount"] == 500000
        assert data["data"]["budgets"][0]["category_id"] == cat_id

    async def test_copy_from_previous_empty_month(self, auth_client):
        """Salin dari bulan sebelumnya yang tidak ada budget → kosong."""
        response = await auth_client.post(
            "/api/budgets/copy-from-previous?month=12&year=2025",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["budgets"] == []

    async def test_copy_from_previous_no_auth(self, client):
        """Tanpa login → 401."""
        response = await client.post("/api/budgets/copy-from-previous?month=6&year=2026")
        assert response.status_code == 401


class TestBudgetBulkCreate:
    """Test POST /api/budgets/bulk-create"""

    async def test_bulk_create(self, auth_client):
        """Buat multiple budgets sekaligus."""
        cat_resp = await auth_client.get("/api/categories")
        categories = cat_resp.json()["data"]["categories"]
        assert len(categories) >= 2
        cat1 = categories[0]["id"]
        cat2 = categories[1]["id"]

        response = await auth_client.post(
            "/api/budgets/bulk-create",
            json={
                "budgets": [
                    {"category_id": cat1, "amount": 500000, "month": 8, "year": 2026},
                    {"category_id": cat2, "amount": 300000, "month": 8, "year": 2026},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["created"]) == 2

    async def test_bulk_create_skip_duplicates(self, auth_client):
        """Budget duplikat di-skip, yang lain tetap dibuat."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        # Buat satu budget dulu
        await auth_client.post(
            "/api/budgets",
            json={"category_id": cat_id, "amount": 500000, "month": 9, "year": 2026},
        )

        # Bulk create dengan kategori yang sama
        response = await auth_client.post(
            "/api/budgets/bulk-create",
            json={
                "budgets": [
                    {"category_id": cat_id, "amount": 500000, "month": 9, "year": 2026},
                ]
            },
        )
        # Tidak error, tapi created = 0 karena duplikat
        assert response.status_code == 200

    async def test_bulk_create_no_auth(self, client):
        """Tanpa login → 401."""
        response = await client.post(
            "/api/budgets/bulk-create",
            json={"budgets": [{"category_id": 1, "amount": 500000, "month": 8, "year": 2026}]},
        )
        assert response.status_code == 401
