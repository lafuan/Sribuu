"""
Service untuk generate laporan PDF bulanan.

Menggunakan ReportLab untuk PDF generation dan Matplotlib untuk chart.
"""

import io
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..models import Budget, Category, Transaction
from ..utils.formatting import BULAN_ID, format_rupiah

logger = logging.getLogger(__name__)

WIB = timezone(timedelta(hours=7))
WIDTH, HEIGHT = A4  # 595.27 x 841.89 points
MARGIN = 2 * cm

# Color palette
GREEN_PRIMARY = "#10b981"
GREEN_DARK = "#059669"
GRAY_TEXT = "#78716c"
GRAY_LIGHT = "#f5f5f4"
GRAY_BORDER = "#e7e5e4"
WHITE = "#ffffff"
BLACK = "#1c1917"
RED_DANGER = "#ef4444"
AMBER = "#f59e0b"

# Category colors for charts
CAT_COLORS = [
    "#10b981", "#059669", "#34d399", "#6ee7b7", "#a7f3d0",
    "#f59e0b", "#f97316", "#ef4444", "#ec4899", "#8b5cf6",
    "#3b82f6", "#06b6d4", "#14b8a6", "#84cc16", "#64748b",
]

FONT_NAME = "Helvetica"


def _today_wib() -> date:
    return datetime.now(WIB).date()


def _start_of_month(year: int, month: int) -> date:
    return date(year, month, 1)


def _end_of_month(year: int, month: int) -> date:
    if month == 12:
        return date(year, month, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _generate_pie_chart(categories: list[dict], total: int) -> io.BytesIO:
    """Generate pie chart as PNG buffer for category breakdown."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5, 4))

    values = [c["total_amount"] for c in categories]
    colors_list = [c["category"].get("color", CAT_COLORS[i % len(CAT_COLORS)])
                   for i, c in enumerate(categories)]

    if not values or sum(values) == 0:
        ax.text(0.5, 0.5, "Tidak ada data", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color=GRAY_TEXT)
        ax.set_aspect("equal")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
        buf.seek(0)
        plt.close(fig)
        return buf

    wedges, texts, autotexts = ax.pie(
        values, labels=None, colors=colors_list,
        autopct=lambda pct: f"{pct:.0f}%" if pct > 5 else "",
        startangle=90, pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )

    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight("bold")
        at.set_color("white")

    # Legend
    legend_labels = [f"{c['category']['icon']} {c['category']['name']} — {c['percentage']}%"
                     for c in categories[:7]]  # max 7 items
    ax.legend(wedges[:7], legend_labels, loc="center left",
              bbox_to_anchor=(1, 0.5), fontsize=8, frameon=False)

    ax.set_aspect("equal")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf


def _generate_bar_chart(daily_data: list[dict], max_amount: int) -> io.BytesIO:
    """Generate bar chart as PNG buffer for daily trend."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 3))

    dates = [d["date_formatted"] for d in daily_data]
    amounts = [d["total_amount"] for d in daily_data]

    if not amounts or max_amount == 0:
        ax.text(0.5, 0.5, "Tidak ada data tren harian", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color=GRAY_TEXT)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
        buf.seek(0)
        plt.close(fig)
        return buf

    bars = ax.bar(dates, amounts, color=GREEN_PRIMARY, edgecolor="white",
                  linewidth=0.5, width=0.6)

    # Highlight today
    if len(bars) > 0:
        bars[-1].set_color(GREEN_DARK)

    ax.set_ylabel("Rupiah", fontsize=8, color=GRAY_TEXT)
    ax.tick_params(axis="x", rotation=45, labelsize=7, colors=GRAY_TEXT)
    ax.tick_params(axis="y", labelsize=7, colors=GRAY_TEXT)

    # Format y-axis as k
    if max_amount > 0:
        from matplotlib.ticker import FuncFormatter
        def _k_format(x, _):
            if x >= 1_000_000:
                return f"{x/1_000_000:.1f}M"
            elif x >= 1_000:
                return f"{x/1_000:.0f}k"
            return str(int(x))
        ax.yaxis.set_major_formatter(FuncFormatter(_k_format))

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRAY_BORDER)
    ax.spines["bottom"].set_color(GRAY_BORDER)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf


async def _get_monthly_data(
    db: AsyncSession, user_id: int, year: int, month: int
) -> dict:
    """Fetch all data needed for monthly PDF report."""
    month_start = _start_of_month(year, month)
    month_end = _end_of_month(year, month)

    # --- Total bulan ini ---
    result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= month_end,
            Transaction.parent_transaction_id.is_(None),
        )
    )
    total_amount, tx_count = result.one()
    total_amount = int(total_amount)

    # --- Daily average ---
    days_in_month = (month_end - month_start).days + 1
    today = _today_wib()
    effective_days = min((today - month_start).days + 1, days_in_month)
    daily_avg = total_amount // effective_days if effective_days > 0 else 0

    # --- Per category breakdown ---
    result = await db.execute(
        select(
            Category.id,
            Category.name,
            Category.icon,
            Category.color,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= month_end,
            Transaction.parent_transaction_id.is_(None),
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
    )

    categories: list[dict] = []
    for row in result.all():
        pct = (row.total / total_amount * 100) if total_amount > 0 else 0
        categories.append({
            "category": {
                "id": row.id,
                "name": row.name,
                "icon": row.icon,
                "color": row.color or CAT_COLORS[len(categories) % len(CAT_COLORS)],
            },
            "total_amount": int(row.total),
            "transaction_count": row.count,
            "percentage": round(pct, 1),
        })

    # --- Daily trend (last 30 days within month) ---
    trend_start = max(month_start, today - timedelta(days=29))
    trend_end = min(today, month_end)

    result = await db.execute(
        select(
            Transaction.transaction_date,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= trend_start,
            Transaction.transaction_date <= trend_end,
            Transaction.parent_transaction_id.is_(None),
        )
        .group_by(Transaction.transaction_date)
        .order_by(Transaction.transaction_date)
    )
    db_data = {row.transaction_date: (int(row.total), row.count) for row in result.all()}

    daily_trend = []
    max_daily = 0
    current = trend_start
    while current <= trend_end:
        total, count = db_data.get(current, (0, 0))
        max_daily = max(max_daily, total)
        daily_trend.append({
            "date": current.isoformat(),
            "date_formatted": f"{current.day:02d}/{current.month:02d}",
            "total_amount": total,
            "transaction_count": count,
        })
        current += timedelta(days=1)

    # --- Budget vs Actual ---
    result = await db.execute(
        select(Budget)
        .options(joinedload(Budget.category))
        .where(
            Budget.user_id == user_id,
            Budget.month == month,
            Budget.year == year,
        )
        .order_by(Budget.category_id)
    )
    budgets = list(result.unique().scalars().all())

    # Get actual spending per budget category
    budget_vs_actual = []
    for budget in budgets:
        cat_spent_result = await db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user_id,
                Transaction.category_id == budget.category_id,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_date <= month_end,
            )
        )
        spent = int(cat_spent_result.scalar() or 0)
        effective_budget = budget.amount + (budget.rollover or 0)
        pct = (spent / effective_budget * 100) if effective_budget > 0 else 0

        budget_vs_actual.append({
            "category_name": budget.category.name if budget.category else "?",
            "category_icon": budget.category.icon if budget.category else "📦",
            "category_color": budget.category.color if budget.category else "#6b7280",
            "budget": budget.amount,
            "rollover": budget.rollover or 0,
            "effective_budget": effective_budget,
            "spent": spent,
            "remaining": effective_budget - spent,
            "percentage": round(pct, 1),
        })

    # --- Comparison with previous month ---
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    prev_start = _start_of_month(prev_year, prev_month)
    prev_end = _end_of_month(prev_year, prev_month)

    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_start,
            Transaction.transaction_date <= prev_end,
            Transaction.parent_transaction_id.is_(None),
        )
    )
    prev_total = int(result.scalar() or 0)

    diff = total_amount - prev_total
    pct_change = round((diff / prev_total * 100), 1) if prev_total > 0 else 0

    # --- Highest transaction ---
    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= month_end,
            Transaction.parent_transaction_id.is_(None),
        )
        .order_by(Transaction.amount.desc())
        .limit(1)
    )
    highest_tx = result.scalar_one_or_none()
    highest = None
    if highest_tx:
        highest = {
            "amount": highest_tx.amount,
            "notes": highest_tx.notes or "",
            "date": highest_tx.transaction_date.isoformat() if highest_tx.transaction_date else "",
            "category_name": highest_tx.category.name if highest_tx.category else "",
            "category_icon": highest_tx.category.icon if highest_tx.category else "",
        }

    return {
        "year": year,
        "month": month,
        "month_label": f"{BULAN_ID[month]} {year}",
        "total_amount": total_amount,
        "transaction_count": tx_count,
        "days_in_month": days_in_month,
        "daily_average": daily_avg,
        "categories": categories,
        "daily_trend": daily_trend,
        "max_daily": max_daily,
        "budget_vs_actual": budget_vs_actual,
        "prev_month_total": prev_total,
        "prev_month_label": f"{BULAN_ID[prev_month]} {prev_year}",
        "difference": diff,
        "percentage_change": pct_change,
        "highest_transaction": highest,
        "generated_at": datetime.now(WIB).strftime("%d %B %Y, %H:%M WIB"),
    }


def _build_pdf(data: dict) -> io.BytesIO:
    """Build PDF from monthly report data using ReportLab."""
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Laporan Keuangan - {data['month_label']}",
        author="Sribuu",
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=20,
        textColor=GREEN_DARK, spaceAfter=4,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10,
        textColor=GRAY_TEXT, spaceAfter=12,
        alignment=TA_CENTER,
    )
    heading2_style = ParagraphStyle(
        "ReportH2", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=14,
        textColor=BLACK, spaceBefore=16, spaceAfter=8,
    )
    normal_style = ParagraphStyle(
        "ReportNormal", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9,
        textColor=BLACK, leading=13,
    )
    small_style = ParagraphStyle(
        "ReportSmall", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7,
        textColor=GRAY_TEXT,
    )
    footer_style = ParagraphStyle(
        "ReportFooter", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7,
        textColor=GRAY_TEXT, alignment=TA_CENTER,
    )

    story = []
    total_amount = data["total_amount"]

    # ===== HEADER =====
    story.append(Paragraph("Laporan Keuangan Bulanan", title_style))
    story.append(Paragraph(data["month_label"], subtitle_style))
    story.append(Paragraph(
        f"Dibuat: {data['generated_at']}",
        ParagraphStyle("GenDate", parent=small_style, alignment=TA_CENTER, spaceAfter=16),
    ))

    # ===== SUMMARY CARDS (as a table) =====
    summary_data = [
        [
            _summary_box("Total Pengeluaran", format_rupiah(total_amount), GREEN_DARK),
            _summary_box("Total Transaksi", str(data["transaction_count"]), GRAY_TEXT),
            _summary_box("Rata-rata/Hari", format_rupiah(data["daily_average"]), GRAY_TEXT),
            _summary_box("Transaksi Tertinggi",
                         format_rupiah(data["highest_transaction"]["amount"]) if data["highest_transaction"] else "—",
                         GRAY_TEXT),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[doc.width/4 - 8]*4)
    summary_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(summary_table)

    # Month-over-month comparison
    if data["prev_month_total"] > 0:
        diff = data["difference"]
        pct = data["percentage_change"]
        direction = "▲" if diff > 0 else "▼" if diff < 0 else "—"
        comp_text = (
            f"{direction} vs {data['prev_month_label']}: "
            f"Rp {abs(diff):,} ({abs(pct)}% "
            f"{'lebih boros' if diff > 0 else 'lebih hemat' if diff < 0 else 'sama'})"
        )
        comp_color = RED_DANGER if diff > 0 else GREEN_DARK if diff < 0 else GRAY_TEXT
        story.append(Spacer(1, 8))
        story.append(Paragraph(comp_text, ParagraphStyle(
            "Comparison", parent=small_style, textColor=comp_color, alignment=TA_CENTER,
        )))

    story.append(Spacer(1, 16))

    # ===== PIE CHART: Distribusi Kategori =====
    story.append(Paragraph("Distribusi Pengeluaran per Kategori", heading2_style))

    if data["categories"] and total_amount > 0:
        pie_buf = _generate_pie_chart(data["categories"], total_amount)
        pie_img = Image(pie_buf, width=doc.width * 0.8, height=doc.width * 0.55)
        pie_img.hAlign = "CENTER"
        story.append(pie_img)

        # Category table
        cat_table_data = [["Kategori", "Jumlah", "%", "Transaksi"]]
        for cat in data["categories"]:
            cat_table_data.append([
                f"{cat['category']['icon']} {cat['category']['name']}",
                format_rupiah(cat["total_amount"]),
                f"{cat['percentage']}%",
                str(cat["transaction_count"]),
            ])

        cat_table = Table(cat_table_data, colWidths=[
            doc.width * 0.4, doc.width * 0.25, doc.width * 0.15, doc.width * 0.2
        ])
        cat_table.setStyle(_table_style(header_rows=1))
        story.append(Spacer(1, 8))
        story.append(cat_table)
    else:
        story.append(Paragraph("Belum ada data untuk periode ini.", normal_style))

    # ===== BAR CHART: Tren Harian =====
    story.append(Paragraph("Tren Pengeluaran Harian", heading2_style))

    if data["daily_trend"] and data["max_daily"] > 0:
        bar_buf = _generate_bar_chart(data["daily_trend"], data["max_daily"])
        bar_img = Image(bar_buf, width=doc.width * 0.95, height=doc.width * 0.35)
        bar_img.hAlign = "CENTER"
        story.append(bar_img)
    else:
        story.append(Paragraph("Belum ada data tren harian.", normal_style))

    story.append(Spacer(1, 8))

    # ===== BUDGET vs ACTUAL =====
    if data["budget_vs_actual"]:
        story.append(Paragraph("Budget vs Realisasi", heading2_style))

        bva_data = [["Kategori", "Budget", "Realisasi", "Sisa", "%"]]
        for b in data["budget_vs_actual"]:
            bva_data.append([
                f"{b['category_icon']} {b['category_name']}",
                format_rupiah(b["effective_budget"]),
                format_rupiah(b["spent"]),
                format_rupiah(b["remaining"]),
                f"{b['percentage']}%",
            ])

        bva_table = Table(bva_data, colWidths=[
            doc.width * 0.3, doc.width * 0.2, doc.width * 0.2, doc.width * 0.2, doc.width * 0.1
        ])
        bva_table.setStyle(_table_style(header_rows=1,
                                        highlight_col=3))  # highlight remaining
        story.append(bva_table)
    else:
        story.append(Paragraph("Budget vs Realisasi", heading2_style))
        story.append(Paragraph("Belum ada budget untuk bulan ini. ", normal_style))
        story.append(Paragraph(
            "Atur budget di menu Budgets untuk melihat perbandingan budget vs actual.",
            small_style,
        ))

    # ===== HIGHEST TRANSACTION =====
    if data["highest_transaction"]:
        story.append(Paragraph("Transaksi Tertinggi Bulan Ini", heading2_style))
        ht = data["highest_transaction"]
        ht_text = (
            f"<b>{ht['category_icon']} {ht['category_name']}</b> — "
            f"<b>{format_rupiah(ht['amount'])}</b><br/>"
            f"Tanggal: {ht['date']}<br/>"
            f"Catatan: {ht['notes'] or '(tanpa catatan)'}"
        )
        story.append(Paragraph(ht_text, normal_style))

    # ===== FOOTER =====
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"Laporan ini dibuat otomatis oleh <b>Sribuu</b> — Aplikasi Pencatatan Pengeluaran Harian<br/>"
        f"© {data['year']} Sribuu. All rights reserved.",
        footer_style,
    ))

    # Build PDF
    doc.build(story)
    buf.seek(0)
    return buf


def _summary_box(label: str, value: str, value_color: str) -> Paragraph:
    """Create a summary card paragraph."""
    return Paragraph(
        f'<para alignment="center">'
        f'<font color="{GRAY_TEXT}" size="7">{label}</font><br/>'
        f'<font color="{value_color}" size="16"><b>{value}</b></font>'
        f'</para>',
        ParagraphStyle("SummaryBox", fontName="Helvetica", leading=16),
    )


def _table_style(header_rows: int = 1, highlight_col: int | None = None) -> TableStyle:
    """Create consistent TableStyle for report tables."""
    commands = [
        # Header
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor(GREEN_PRIMARY)),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.white),
        ("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, header_rows - 1), 9),
        # Data rows
        ("FONTNAME", (0, header_rows), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, header_rows), (-1, -1), 8),
        ("TEXTCOLOR", (0, header_rows), (-1, -1), colors.HexColor(BLACK)),
        # Alignment
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(GRAY_BORDER)),
        ("LINEBELOW", (0, 0), (-1, header_rows - 1), 1.5, colors.HexColor(GREEN_DARK)),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        # Alternating row colors
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [colors.white, colors.HexColor(GRAY_LIGHT)]),
    ]

    if highlight_col is not None:
        # Color the "remaining" column green/red based on value (handled during table build)
        pass

    return TableStyle(commands)


async def generate_monthly_report_pdf(
    db: AsyncSession,
    user_id: int,
    year: int | None = None,
    month: int | None = None,
) -> tuple[str, io.BytesIO]:
    """Generate PDF report for a specific month.

    Returns (filename, BytesIO buffer)."""
    today = _today_wib()
    if not year:
        year = today.year
    if not month:
        month = today.month

    data = await _get_monthly_data(db, user_id, year, month)

    if data["total_amount"] == 0 and data["transaction_count"] == 0:
        # Still generate PDF but with "no data" message
        pass

    pdf_buf = _build_pdf(data)
    filename = f"laporan_sribuu_{year}_{month:02d}.pdf"

    return filename, pdf_buf
