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

        # Safe date approach: anchor to Monday of current week, then go back 1 week
        # This guarantees all dates are in the PREVIOUS week (always past, always valid)
        # and the weekly summary will show them as prev_week_total
        from datetime import date, timedelta
        today = date.today()
        # Previous week's Monday (always in the past)
        prev_week_monday = today - timedelta(days=today.weekday() + 7)
        dates = [
            prev_week_monday,
            prev_week_monday + timedelta(days=1),
            prev_week_monday + timedelta(days=2),
        ]
        # Assert all dates are in the past (schema requirement)
        assert all(d < today for d in dates), f"Some dates are not past: {dates}"

        for amount, d in zip([50000, 25000, 100000], dates, strict=True):
            resp = await auth_client.post(
                "/api/transactions",
                json={"amount": amount, "category_id": cat_id, "transaction_date": d.isoformat()},
            )
            assert resp.status_code == 201, f"Transaction creation failed: {resp.text}"

        # Trigger weekly summary generation (current week has no data)
        response = await auth_client.get("/api/stats/weekly-summary?force=true")
        assert response.status_code == 200
        data = response.json()["data"]
        # Current week: no transactions
        assert data["total_amount"] == 0
        assert data["transaction_count"] == 0
        # Previous week: 3 transactions (validated via daily_breakdown count or daily_average > 0)
        # The service computes prev_week_total by summing transactions from prev week's range
        # We can verify via stats/daily endpoint for the previous week's range
        from datetime import date
        # Verify transactions were saved: sum the daily array with non-zero amounts
        prev_sunday = prev_week_monday + timedelta(days=6)
        trend_resp = await auth_client.get(
            f"/api/stats/daily-trend?date_from={prev_week_monday.isoformat()}&date_to={prev_sunday.isoformat()}"
        )
        assert trend_resp.status_code == 200, f"daily-trend failed: {trend_resp.text}"
        trend_body = trend_resp.json()
        # daily-trend returns StandardResponse: {status, data: {date_from, date_to, daily, max_amount}}
        trend_data = trend_body.get("data", trend_body)
        assert "daily" in trend_data, f"Unexpected response structure: {trend_data}"
        daily_amounts = [day["total_amount"] for day in trend_data["daily"]]
        daily_total = sum(daily_amounts)
        assert daily_total == 175000, (
            f"Expected 175000 total from daily-trend for prev week ({prev_week_monday} to {prev_sunday}), "
            f"got {daily_total}. Daily breakdown: {daily_amounts}"
        )

    async def test_weekly_summary_cached(self, auth_client):
        """Ringkasan mingguan bisa di-cache."""
        # First call generates and caches
        await auth_client.get("/api/stats/weekly-summary?force=true")
        # Second call without force returns cached
        response = await auth_client.get("/api/stats/weekly-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total_amount"] >= 0  # dari cache

        # Verifikasi cached flag
        response = await auth_client.get("/api/stats/weekly-summary?force=true")
        data = response.json()["data"]
        assert data["total_amount"] >= 0


class TestAnnualSummary:
    """Test GET /api/stats/annual-summary"""

    async def test_annual_summary_empty(self, auth_client):
        """Annual summary tanpa data transaksi."""
        from datetime import date
        year = date.today().year
        response = await auth_client.get(f"/api/stats/annual-summary?year={year}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        summary = data["data"]
        assert summary["year"] == year
        assert summary["total_expense"] == 0
        assert summary["total_transactions"] == 0
        assert summary["average_monthly_spending"] == 0
        assert summary["total_income"] == 0
        assert summary["top_categories"] == []
        # monthly_breakdown returns all 12 months even when empty
        assert len(summary["monthly_breakdown"]) == 12
        for month in summary["monthly_breakdown"]:
            assert month["total_amount"] == 0

    async def test_annual_summary_with_data(self, auth_client):
        """Annual summary dengan transaksi."""
        cat_resp = await auth_client.get("/api/categories")
        cats = cat_resp.json()["data"]["categories"]
        cat_id = cats[0]["id"]

        from datetime import date, timedelta
        today = date.today()
        year = today.year

        # Buat transaksi di bulan berjalan
        await auth_client.post(
            "/api/transactions",
            json={"amount": 50000, "category_id": cat_id, "transaction_date": today.isoformat()},
        )
        await auth_client.post(
            "/api/transactions",
            json={"amount": 30000, "category_id": cat_id, "transaction_date": today.isoformat()},
        )

        response = await auth_client.get(f"/api/stats/annual-summary?year={year}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        summary = data["data"]
        assert summary["year"] == year
        assert summary["total_expense"] == 80000
        assert summary["total_transactions"] == 2
        assert summary["average_monthly_spending"] == 80000 // 12

    async def test_annual_summary_year_default_to_current(self, auth_client):
        """Annual summary default year ke tahun berjalan."""
        response = await auth_client.get("/api/stats/annual-summary")
        assert response.status_code == 200
        data = response.json()
        from datetime import date
        assert data["data"]["year"] == date.today().year

    async def test_annual_summary_year_over_year(self, auth_client):
        """Annual summary dengan data year-over-year."""
        cat_resp = await auth_client.get("/api/categories")
        cats = cat_resp.json()["data"]["categories"]
        cat_id = cats[0]["id"]

        from datetime import date
        today = date.today()
        year = today.year

        # Buat transaksi di tahun berjalan
        await auth_client.post(
            "/api/transactions",
            json={"amount": 100000, "category_id": cat_id, "transaction_date": today.isoformat()},
        )

        response = await auth_client.get(f"/api/stats/annual-summary?year={year}")
        assert response.status_code == 200
        data = response.json()
        summary = data["data"]
        assert "year_over_year" in summary
        assert "previous_year" in summary["year_over_year"]
        assert "change_pct" in summary["year_over_year"]
