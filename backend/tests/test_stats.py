"""Tests untuk modul statistik: summary, by-category, daily-trend, monthly."""


class TestStatsSummary:
    """Test GET /api/stats/summary"""

    async def test_summary_empty(self, auth_client):
        """Dashboard saat belum ada transaksi."""
        response = await auth_client.get("/api/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["today"]["total_amount"] == 0
        assert data["data"]["today"]["transaction_count"] == 0
        assert data["data"]["this_month"]["total_amount"] == 0
        assert len(data["data"]["recent_transactions"]) == 0

    async def test_summary_with_data(self, auth_client):
        """Dashboard setelah ada transaksi."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        # Buat 2 transaksi hari ini
        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={"amount": 25000, "category_id": cat_id, "transaction_date": today},
        )
        await auth_client.post(
            "/api/transactions",
            json={"amount": 15000, "category_id": cat_id, "transaction_date": today},
        )

        response = await auth_client.get("/api/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["today"]["total_amount"] == 40000
        assert data["data"]["today"]["transaction_count"] == 2
        assert data["data"]["this_month"]["total_amount"] == 40000
        assert len(data["data"]["recent_transactions"]) >= 2


class TestStatsByCategory:
    """Test GET /api/stats/by-category"""

    async def test_by_category_empty(self, auth_client):
        """By-category tanpa data transaksi."""
        response = await auth_client.get("/api/stats/by-category")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total_amount"] == 0
        assert len(data["data"]["categories"]) == 0

    async def test_by_category_with_data(self, auth_client):
        """By-category dengan data transaksi."""
        cat_resp = await auth_client.get("/api/categories")
        cats = cat_resp.json()["data"]["categories"]

        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={"amount": 50000, "category_id": cats[0]["id"], "transaction_date": today},
        )
        await auth_client.post(
            "/api/transactions",
            json={"amount": 30000, "category_id": cats[1]["id"], "transaction_date": today},
        )

        response = await auth_client.get("/api/stats/by-category")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_amount"] == 80000
        assert len(data["data"]["categories"]) >= 2


class TestDailyTrend:
    """Test GET /api/stats/daily-trend"""

    async def test_daily_trend_empty(self, auth_client):
        """Daily trend tanpa data."""
        response = await auth_client.get("/api/stats/daily-trend")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["daily"]) >= 7  # 7 hari terakhir meski kosong

    async def test_daily_trend_with_data(self, auth_client):
        """Daily trend dengan data."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date, timedelta
        today = date.today()

        for i in range(3):
            d = today - timedelta(days=i)
            await auth_client.post(
                "/api/transactions",
                json={"amount": 10000 * (i + 1), "category_id": cat_id,
                      "transaction_date": d.isoformat()},
            )

        response = await auth_client.get("/api/stats/daily-trend")
        assert response.status_code == 200
        data = response.json()
        # Harus ada hari dengan total > 0
        totals = [d["total_amount"] for d in data["data"]["daily"]]
        assert sum(totals) == 60000


class TestMonthlyStats:
    """Test GET /api/stats/monthly"""

    async def test_monthly_empty(self, auth_client):
        """Monthly stats tanpa data."""
        response = await auth_client.get("/api/stats/monthly")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total_amount"] == 0
        assert data["data"]["transaction_count"] == 0

    async def test_monthly_with_data(self, auth_client):
        """Monthly stats dengan data."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today()

        await auth_client.post(
            "/api/transactions",
            json={"amount": 100000, "category_id": cat_id, "transaction_date": today.isoformat()},
        )

        response = await auth_client.get(f"/api/stats/monthly?year={today.year}&month={today.month}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_amount"] == 100000
        assert data["data"]["transaction_count"] == 1


class TestMonthlyComparison:
    """Test GET /api/stats/monthly-comparison"""

    async def test_monthly_comparison(self, auth_client):
        """Monthly comparison (default 3 bulan)."""
        response = await auth_client.get("/api/stats/monthly-comparison")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["months"]) >= 1  # Minimal bulan ini
        # Setiap bulan punya struktur yang benar
        for m in data["data"]["months"]:
            assert "year" in m
            assert "month" in m
            assert "total_amount" in m
            assert "transaction_count" in m

    async def test_monthly_comparison_custom_months(self, auth_client):
        """Monthly comparison dengan custom months=6."""
        response = await auth_client.get("/api/stats/monthly-comparison?months=6")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["months"]) == 6


class TestSpendingPace:
    """Test GET /api/stats/spending-pace"""

    async def test_pace_no_data_no_budget(self, auth_client):
        """Spending pace tanpa transaksi dan tanpa budget."""
        response = await auth_client.get("/api/stats/spending-pace")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        pace = data["data"]
        assert pace["total_spent"] == 0
        assert pace["daily_avg"] == 0
        assert pace["projected_total"] == 0
        assert pace["total_budget"] == 0
        assert pace["budget_used_pct"] is None
        assert pace["is_on_track"] is None
        assert pace["days_elapsed"] >= 1
        assert pace["time_elapsed_pct"] > 0

    async def test_pace_with_transactions_no_budget(self, auth_client):
        """Spending pace dengan transaksi tapi tanpa budget."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today().isoformat()

        await auth_client.post(
            "/api/transactions",
            json={"amount": 50000, "category_id": cat_id, "transaction_date": today},
        )

        response = await auth_client.get("/api/stats/spending-pace")
        assert response.status_code == 200
        pace = response.json()["data"]
        assert pace["total_spent"] == 50000
        assert pace["daily_avg"] >= 1
        assert pace["projected_total"] > 0
        assert pace["total_budget"] == 0
        assert pace["budget_used_pct"] is None
        assert pace["is_on_track"] is None

    async def test_pace_on_track(self, auth_client):
        """Spending pace on track (budget cukup)."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today()

        # Buat transaksi kecil
        await auth_client.post(
            "/api/transactions",
            json={"amount": 10000, "category_id": cat_id, "transaction_date": today.isoformat()},
        )

        # Set budget besar agar on track
        await auth_client.post(
            "/api/budgets",
            json={
                "category_id": cat_id,
                "amount": 999999999,
                "month": today.month,
                "year": today.year,
            },
        )

        response = await auth_client.get("/api/stats/spending-pace")
        assert response.status_code == 200
        pace = response.json()["data"]
        assert pace["total_budget"] > 0
        assert pace["budget_used_pct"] is not None
        assert pace["is_on_track"] is True

    async def test_pace_over_pace(self, auth_client):
        """Spending pace over pace (melebihi budget)."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date
        today = date.today()

        # Set budget sangat kecil
        await auth_client.post(
            "/api/budgets",
            json={
                "category_id": cat_id,
                "amount": 1000,
                "month": today.month,
                "year": today.year,
            },
        )

        # Transaksi besar
        await auth_client.post(
            "/api/transactions",
            json={"amount": 50000, "category_id": cat_id, "transaction_date": today.isoformat()},
        )

        response = await auth_client.get("/api/stats/spending-pace")
        assert response.status_code == 200
        pace = response.json()["data"]
        assert pace["total_budget"] > 0
        assert pace["budget_used_pct"] is not None
        # Budget terpakai harus > waktu berlalu
        assert pace["is_on_track"] is False

    async def test_pace_custom_month(self, auth_client):
        """Spending pace dengan custom month/year."""
        response = await auth_client.get("/api/stats/spending-pace?month=1&year=2025")
        assert response.status_code == 200
        pace = response.json()["data"]
        assert pace["month"] == 1
        assert pace["year"] == 2025
        assert pace["days_in_month"] == 31

    async def test_pace_htmx_request(self, auth_client):
        """Spending pace dengan HTMX header returns HTML."""
        response = await auth_client.get(
            "/api/stats/spending-pace",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    async def test_pace_with_multiple_transactions(self, auth_client):
        """Spending pace dengan multiple transactions memverifikasi daily avg."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]

        from datetime import date, timedelta
        today = date.today()

        # Buat 3 transaksi pada hari berbeda (pastikan berbeda)
        for i in range(3):
            d = today - timedelta(days=i)
            await auth_client.post(
                "/api/transactions",
                json={"amount": 15000, "category_id": cat_id, "transaction_date": d.isoformat()},
            )

        response = await auth_client.get("/api/stats/spending-pace")
        assert response.status_code == 200
        pace = response.json()["data"]
        assert pace["total_spent"] == 45000
        assert pace["daily_avg"] == 45000 // pace["days_elapsed"]
        assert pace["remaining_days"] >= 0


class TestWeeklySummary:
    """Test GET /api/stats/weekly-summary"""

    async def test_weekly_summary_empty(self, auth_client):
        """Ringkasan mingguan saat belum ada transaksi."""
        response = await auth_client.get("/api/stats/weekly-summary?force=true")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total_amount"] == 0
        assert data["data"]["transaction_count"] == 0
        assert data["data"]["categories"] == []
        assert data["data"]["top_transactions"] == []
        assert data["data"]["week"] >= 1  # ISO week valid
    
    async def test_weekly_summary_with_data(self, auth_client):
        """Ringkasan mingguan dengan transaksi."""
        cat_resp = await auth_client.get("/api/categories")
        cat_id = cat_resp.json()["data"]["categories"][0]["id"]
        
        from datetime import date, timedelta
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        
        # Buat 3 transaksi minggu ini
        for amount, day_offset in [(50000, 0), (25000, 1), (100000, 2)]:
            d = monday + timedelta(days=day_offset)
            await auth_client.post(
                "/api/transactions",
                json={"amount": amount, "category_id": cat_id, "transaction_date": d.isoformat()},
            )
        
        response = await auth_client.get("/api/stats/weekly-summary?force=true")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_amount"] == 175000
        assert data["transaction_count"] == 3
        assert len(data["categories"]) >= 1
        assert len(data["top_transactions"]) == 3
        assert data["top_transactions"][0]["amount"] == 100000  # sorted desc
    
    async def test_weekly_summary_cached(self, auth_client):
        """Ringkasan mingguan bisa di-cache."""
        response = await auth_client.get("/api/stats/weekly-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
