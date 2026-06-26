"""
Tests untuk Bill Service.
"""

from datetime import date

import pytest

from backend.database import AsyncSessionLocal
from backend.models import Bill, User
from backend.schemas.bill import BillCreate, BillUpdate
from backend.services.bill_service import (
    create_bill,
    delete_bill,
    get_upcoming_bills,
    list_bills,
    mark_as_paid,
    unmark_paid,
    update_bill,
)


@pytest.fixture
async def test_user():
    async with AsyncSessionLocal() as db:
        from backend.services.auth_service import hash_password
        user = User(
            name="Bill Tester",
            email="billtest@test.com",
            password_hash=hash_password("test123"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        yield user
        await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
class TestBillCRUD:
    async def test_create_bill(self, test_user):
        async with AsyncSessionLocal() as db:
            data = BillCreate(
                name="Listrik",
                amount=250000,
                due_date=date(2026, 7, 1),
                frequency="monthly",
                category_id=4,
            )
            bill = await create_bill(db, test_user.id, data)
            await db.commit()
            assert bill["name"] == "Listrik"
            assert bill["amount"] == 250000
            assert bill["frequency"] == "monthly"
            assert not bill["is_paid"]

            # Cleanup
            b = await db.get(Bill, bill["id"])
            await db.delete(b)
            await db.commit()

    async def test_list_bills(self, test_user):
        async with AsyncSessionLocal() as db:
            data = BillCreate(
                name="Internet",
                amount=150000,
                due_date=date(2026, 7, 5),
                frequency="monthly",
                category_id=4,
            )
            bill = await create_bill(db, test_user.id, data)
            await db.commit()

            bills = await list_bills(db, test_user.id)
            assert len(bills) > 0

            # Cleanup
            b = await db.get(Bill, bill["id"])
            await db.delete(b)
            await db.commit()

    async def test_update_bill(self, test_user):
        async with AsyncSessionLocal() as db:
            data = BillCreate(
                name="Air",
                amount=100000,
                due_date=date(2026, 7, 10),
                frequency="monthly",
                category_id=4,
            )
            bill = await create_bill(db, test_user.id, data)
            await db.commit()

            update_data = BillUpdate(name="Air PDAM", amount=120000, due_date=None, frequency=None, category_id=None)
            updated = await update_bill(db, bill["id"], test_user.id, update_data)
            await db.commit()
            assert updated["name"] == "Air PDAM"
            assert updated["amount"] == 120000

            # Cleanup
            b = await db.get(Bill, bill["id"])
            await db.delete(b)
            await db.commit()

    async def test_delete_bill(self, test_user):
        async with AsyncSessionLocal() as db:
            data = BillCreate(
                name="Sewa",
                amount=3000000,
                due_date=date(2026, 7, 1),
                frequency="yearly",
                category_id=4,
            )
            bill = await create_bill(db, test_user.id, data)
            await db.commit()

            await delete_bill(db, bill["id"], test_user.id)
            await db.commit()

            b = await db.get(Bill, bill["id"])
            assert b is None

    async def test_get_upcoming_bills(self, test_user):
        async with AsyncSessionLocal() as db:
            data = BillCreate(
                name="Kartu Kredit",
                amount=500000,
                due_date=date(2026, 6, 28),
                frequency="monthly",
                category_id=4,
            )
            bill = await create_bill(db, test_user.id, data)
            await db.commit()

            upcoming = await get_upcoming_bills(db, test_user.id)
            # Should include our bill (due_date June 28 is before today June 26? No — it's after)
            # June 28 > June 26, so it's upcoming, not overdue
            assert len(upcoming) >= 1

            # Cleanup
            b = await db.get(Bill, bill["id"])
            await db.delete(b)
            await db.commit()

    async def test_mark_as_paid(self, test_user):
        async with AsyncSessionLocal() as db:
            data = BillCreate(
                name="Listrik",
                amount=250000,
                due_date=date(2026, 7, 1),
                frequency="monthly",
                category_id=4,
            )
            bill = await create_bill(db, test_user.id, data)
            await db.commit()

            # Mark as paid
            paid = await mark_as_paid(db, bill["id"], test_user.id, payment_method_id=1)
            await db.commit()
            assert paid["is_paid"] is True
            assert paid["paid_transaction_id"] is not None

            # Unmark
            unpaid = await unmark_paid(db, bill["id"], test_user.id)
            await db.commit()
            assert unpaid["is_paid"] is False
            assert unpaid["paid_transaction_id"] is None

            # Cleanup
            b = await db.get(Bill, bill["id"])
            await db.delete(b)
            await db.commit()

    async def test_mark_already_paid_fails(self, test_user):
        async with AsyncSessionLocal() as db:
            data = BillCreate(
                name="Internet",
                amount=150000,
                due_date=date(2026, 7, 5),
                frequency="monthly",
                category_id=4,
            )
            bill = await create_bill(db, test_user.id, data)
            await db.commit()

            await mark_as_paid(db, bill["id"], test_user.id, payment_method_id=1)
            await db.commit()

            from fastapi import HTTPException
            with pytest.raises(HTTPException):
                await mark_as_paid(db, bill["id"], test_user.id, payment_method_id=1)

            # Cleanup
            b = await db.get(Bill, bill["id"])
            await db.delete(b)
            await db.commit()
