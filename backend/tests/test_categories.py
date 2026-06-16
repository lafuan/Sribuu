"""Tests untuk modul kategori: list, create, update, delete, toggle."""


class TestListCategories:
    """Test GET /api/categories"""

    async def test_list_with_defaults(self, auth_client):
        """List kategori dengan default seeded → 200, ada data."""
        response = await auth_client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        categories = data["data"]["categories"]
        assert len(categories) >= 10  # Minimal 10 kategori default
        for cat in categories:
            assert "id" in cat
            assert "name" in cat
            assert "icon" in cat
            assert "color" in cat
            assert "is_default" in cat
            assert "is_active" in cat

    async def test_list_active_only(self, auth_client):
        """Default: hanya kategori aktif yang muncul."""
        response = await auth_client.get("/api/categories")
        categories = response.json()["data"]["categories"]
        for cat in categories:
            assert cat["is_active"] is True

    async def test_list_include_inactive(self, auth_client):
        """Dengan include_inactive=true, semua kategori muncul."""
        response = await auth_client.get("/api/categories?include_inactive=true")
        # Saat ini semua default aktif, jadi jumlah sama
        assert response.status_code == 200


class TestCreateCategory:
    """Test POST /api/categories"""

    async def test_create_custom(self, auth_client):
        """Buat kategori kustom → 201."""
        response = await auth_client.post(
            "/api/categories",
            json={
                "name": "Hobi Baru",
                "icon": "🎯",
                "color": "#ff5500",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "Hobi Baru"
        assert data["data"]["icon"] == "🎯"
        assert data["data"]["is_default"] is False
        assert data["data"]["is_active"] is True

    async def test_create_duplicate_name(self, auth_client):
        """Buat kategori dengan nama yang sama → 409."""
        await auth_client.post(
            "/api/categories",
            json={"name": "UniqueCat", "icon": "🎯", "color": "#ff5500"},
        )
        response = await auth_client.post(
            "/api/categories",
            json={"name": "UniqueCat", "icon": "🎯", "color": "#ff5500"},
        )
        assert response.status_code == 409


class TestUpdateCategory:
    """Test PUT /api/categories/{id}"""

    async def test_update_custom(self, auth_client):
        """Update kategori kustom → 200."""
        create_resp = await auth_client.post(
            "/api/categories",
            json={"name": "Old Name", "icon": "🎯", "color": "#ff5500"},
        )
        cat_id = create_resp.json()["data"]["id"]

        response = await auth_client.put(
            f"/api/categories/{cat_id}",
            json={"name": "New Name", "icon": "✨", "color": "#00ff55"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "New Name"
        assert data["data"]["icon"] == "✨"

    async def test_update_default_forbidden(self, auth_client):
        """Update kategori default → 403."""
        cats = (await auth_client.get("/api/categories")).json()["data"]["categories"]
        default_cat = next(c for c in cats if c["is_default"])

        response = await auth_client.put(
            f"/api/categories/{default_cat['id']}",
            json={"name": "Hacked", "icon": "💀", "color": "#000000"},
        )
        assert response.status_code == 403


class TestDeleteCategory:
    """Test DELETE /api/categories/{id}"""

    async def test_delete_unused_custom(self, auth_client):
        """Hapus kategori kustom yang belum dipakai → 200."""
        create_resp = await auth_client.post(
            "/api/categories",
            json={"name": "ToDelete", "icon": "🗑️", "color": "#999999"},
        )
        cat_id = create_resp.json()["data"]["id"]

        response = await auth_client.delete(f"/api/categories/{cat_id}")
        assert response.status_code == 200

    async def test_delete_used_category(self, auth_client):
        """Hapus kategori yang sudah dipakai transaksi → 409."""
        # Buat kategori
        create_resp = await auth_client.post(
            "/api/categories",
            json={"name": "UsedCat", "icon": "📌", "color": "#123456"},
        )
        cat_id = create_resp.json()["data"]["id"]

        # Pakai di transaksi
        await auth_client.post(
            "/api/transactions",
            json={"amount": 10000, "category_id": cat_id, "transaction_date": "2026-06-15"},
        )

        # Coba hapus
        response = await auth_client.delete(f"/api/categories/{cat_id}")
        assert response.status_code == 409

    async def test_delete_default_forbidden(self, auth_client):
        """Hapus kategori default → 403."""
        cats = (await auth_client.get("/api/categories")).json()["data"]["categories"]
        default_cat = next(c for c in cats if c["is_default"])

        response = await auth_client.delete(f"/api/categories/{default_cat['id']}")
        assert response.status_code == 403


class TestToggleCategory:
    """Test PATCH /api/categories/{id}/toggle"""

    async def test_toggle_active(self, auth_client):
        """Toggle kategori: aktif ↔ nonaktif."""
        create_resp = await auth_client.post(
            "/api/categories",
            json={"name": "ToggleMe", "icon": "🔄", "color": "#abcdef"},
        )
        cat_id = create_resp.json()["data"]["id"]

        # Toggle: nonaktifkan
        resp1 = await auth_client.patch(f"/api/categories/{cat_id}/toggle")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["data"]["is_active"] is False

        # Toggle: aktifkan kembali
        resp2 = await auth_client.patch(f"/api/categories/{cat_id}/toggle")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["data"]["is_active"] is True
