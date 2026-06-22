"""
Service untuk export CSV dan JSON.
"""

import csv
import io
import json
import re
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..services.transaction_service import get_transactions_for_export


def extract_tags(notes: str | None) -> list[str]:
    """Extract #hashtags from notes field."""
    if not notes:
        return []
    return re.findall(r"#(\w+)", notes)


def generate_csv(transactions: list, metadata: dict | None = None) -> str:
    """Generate CSV string dari list transaksi.

    Encoding: UTF-8 dengan BOM (agar Excel bisa membaca).
    Includes summary metadata as CSV comments at the top.
    """
    output = io.StringIO()
    # Tulis BOM
    output.write("\ufeff")

    # Summary metadata as CSV comments
    if metadata:
        output.write(f"# Total Transaksi: {metadata.get('total_count', len(transactions))}\n")
        if metadata.get("date_from") and metadata.get("date_to"):
            output.write(f"# Rentang Tanggal: {metadata['date_from']} s/d {metadata['date_to']}\n")
        elif metadata.get("date_from"):
            output.write(f"# Dari Tanggal: {metadata['date_from']}\n")
        elif metadata.get("date_to"):
            output.write(f"# Sampai Tanggal: {metadata['date_to']}\n")
        output.write(f"# Tanggal Export: {metadata.get('export_date', datetime.now().strftime('%Y-%m-%d'))}\n")
        output.write(f"# Total Amount: Rp {metadata.get('total_amount', 0):,.0f}\n")
        output.write("#\n")

    writer = csv.writer(output)

    # Header - matching spec: date, description, amount, category, wallet, notes, tags
    writer.writerow(["Tanggal", "Deskripsi", "Jumlah", "Kategori", "Metode Pembayaran", "Catatan", "Tags"])

    # Data rows
    total_amount = 0
    for tx in transactions:
        category_name = tx.category.name if tx.category else ""
        payment_name = tx.payment_method.name if tx.payment_method else ""
        notes = tx.notes or ""
        tags = extract_tags(notes)
        tags_str = ", ".join(f"#{t}" for t in tags)

        writer.writerow([
            tx.transaction_date.isoformat() if tx.transaction_date else "",
            notes,  # Deskripsi = notes
            tx.amount,
            category_name,
            payment_name,
            notes,
            tags_str,
        ])
        total_amount += tx.amount

    return output.getvalue()


def generate_json(transactions: list, metadata: dict | None = None) -> str:
    """Generate JSON string dari list transaksi.

    Includes summary metadata.
    """
    data = []

    for tx in transactions:
        notes = tx.notes or ""
        tags = extract_tags(notes)

        data.append({
            "date": tx.transaction_date.isoformat() if tx.transaction_date else None,
            "description": notes,
            "amount": tx.amount,
            "category": tx.category.name if tx.category else None,
            "category_icon": tx.category.icon if tx.category else None,
            "payment_method": tx.payment_method.name if tx.payment_method else None,
            "notes": notes,
            "tags": tags,
        })

    total_amount = sum(tx.amount for tx in transactions)

    result = {
        "metadata": {
            "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_transactions": len(transactions),
            "total_amount": total_amount,
            "date_from": metadata.get("date_from") if metadata else None,
            "date_to": metadata.get("date_to") if metadata else None,
        } if metadata or transactions else None,
        "transactions": data,
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


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

    # Build metadata
    total_amount = sum(tx.amount for tx in transactions)
    metadata = {
        "total_count": len(transactions),
        "total_amount": total_amount,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "export_date": today,
    }

    csv_content = generate_csv(transactions, metadata)
    return filename, csv_content


async def export_json(
    db: AsyncSession,
    user_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    payment_method_id: int | None = None,
    search: str | None = None,
) -> tuple[str, str] | None:
    """Export transaksi ke JSON. Return (filename, json_content) atau None jika kosong."""
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
    filename = f"pengeluaran_{today}.json"

    # Build metadata
    metadata = {
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }

    json_content = generate_json(transactions, metadata)
    return filename, json_content
