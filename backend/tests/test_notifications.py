"""
Tests for notification preferences API.
"""


class TestNotificationPreferences:
    """Test GET/POST /api/notifications/preferences."""

    async def test_get_default_preferences(self, auth_client):
        """Default: notification_enabled=false, reminder_time=20:00."""
        resp = await auth_client.get("/api/notifications/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["notification_enabled"] is False
        assert data["reminder_time"] == "20:00"

    async def test_enable_notifications(self, auth_client):
        """Enable notifications dengan reminder_time custom."""
        resp = await auth_client.post(
            "/api/notifications/preferences",
            data={"notification_enabled": "1", "reminder_time": "07:30"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["notification_enabled"] is True
        assert data["reminder_time"] == "07:30"

    async def test_disable_notifications(self, auth_client):
        """Set notification_enabled ke false."""
        # First enable
        await auth_client.post(
            "/api/notifications/preferences",
            data={"notification_enabled": "1", "reminder_time": "20:00"},
        )
        # Then disable
        resp = await auth_client.post(
            "/api/notifications/preferences",
            data={"notification_enabled": "0", "reminder_time": "20:00"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["notification_enabled"] is False

    async def test_invalid_reminder_time_falls_back(self, auth_client):
        """Reminder time invalid harus fallback ke 20:00."""
        resp = await auth_client.post(
            "/api/notifications/preferences",
            data={"notification_enabled": "1", "reminder_time": "invalid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reminder_time"] == "20:00"

    async def test_get_preferences_requires_auth(self, client):
        """Endpoint tanpa auth harus return 401."""
        resp = await client.get("/api/notifications/preferences")
        assert resp.status_code == 401

    async def test_update_preferences_requires_auth(self, client):
        """POST tanpa auth harus return 401."""
        resp = await client.post(
            "/api/notifications/preferences",
            data={"notification_enabled": "1", "reminder_time": "20:00"},
        )
        assert resp.status_code == 401


class TestCheckBudgets:
    """Test GET /api/notifications/check-budgets."""

    async def test_no_budgets_returns_empty(self, auth_client):
        """Check budget tanpa budget harus return []."""
        resp = await auth_client.get("/api/notifications/check-budgets")
        assert resp.status_code == 200
        data = resp.json()
        assert data["alerts"] == []

    async def test_requires_auth(self, client):
        """Check budget tanpa auth harus 401."""
        resp = await client.get("/api/notifications/check-budgets")
        assert resp.status_code == 401

    async def test_budget_below_threshold_no_alert(self, auth_client, db_session):
        """Budget dengan penggunaan di bawah 80% tidak menghasilkan alert."""
        from datetime import date

        from backend.models import Budget, Category

        today = date.today()
        # Get a default category
        cat_result = await db_session.execute(
            __import__("sqlalchemy").select(Category).where(Category.is_default == 1)
        )
        category = cat_result.scalars().first()

        # Get user ID from auth_client's cookie
        from backend.utils.security import verify_access_token
        token = auth_client.cookies.get("access_token")
        payload = verify_access_token(token)
        user_id = int(payload["sub"])

        # Create a budget with very high amount
        budget = Budget(
            user_id=user_id,
            category_id=category.id,
            month=today.month,
            year=today.year,
            amount=100_000_000,  # 100 juta — way above any spending
        )
        db_session.add(budget)
        await db_session.commit()

        resp = await auth_client.get("/api/notifications/check-budgets")
        assert resp.status_code == 200
        data = resp.json()
        # No transactions yet, so spent=0, way below 80%
        assert len(data["alerts"]) == 0
