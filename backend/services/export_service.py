"""
Service untuk export CSV.
"""

import csv
import io
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..services.transaction_service import get_transactions_for_export


def generate_csv(transactions: list) -> str:
    """Generate CSV string dari list transaksi.

    Encoding: UTF-8 dengan BOM (agar Excel bisa membaca).
    """
    output = io.StringIO()
    # Tulis BOM
    output.write("\ufeff")

    writer = csv.writer(output)

    # Header
    writer.writerow(["Tanggal", "Kategori", "Jumlah", "Metode Pembayaran", "Catatan"])

    # Data rows
    for tx in transactions:
        category_name = tx.category.name if tx.category else ""
        payment_name = tx.payment_method.name if tx.payment_method else ""
        notes = tx.notes or ""

        writer.writerow([
            tx.transaction_date.isoformat() if tx.transaction_date else "",
            category_name,
            tx.amount,
            payment_name,
            notes,
        ])

    return output.getvalue()


async def export_csv(
    db: AsyncSession,
    user_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    payment_method_id: int | None = None,
    search: str | None = None,
) -> tuple[str, str] | None:
    """Export transaksi ke CSV. Return (filename, csv_content) atau None jika kosong."""
    transactions = await get_transactions_for_export(
        db=db,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        payment_method_id=payment_method_id,
        search=search,
    )

    if not transactions:
        return None

    # Buat nama file
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"pengeluaran_{today}.csv"

    csv_content = generate_csv(transactions)
    return filename, csv_content
