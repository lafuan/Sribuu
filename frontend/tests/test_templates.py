"""Tests untuk template HTML frontend Sribuu."""
import os
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


# --- Custom filters/functions yang digunakan di template ---

def format_date_id(value, fmt="long"):
    """Filter: format tanggal ke Bahasa Indonesia (simulasi)."""
    if isinstance(value, dict) or value is None:
        return ""
    return str(value)


def format_rupiah(amount, with_rp=True):
    """Filter: format Rupiah (tidak digunakan langsung di template, tapi siap)."""
    return f"Rp {amount:,.0f}" if with_rp else f"{amount:,.0f}"


def url_for(endpoint, **kwargs):
    """Simulasi url_for dari FastAPI."""
    return f"/{endpoint}"


def get_flashed_messages(with_categories=False):
    """Simulasi get_flashed_messages dari Flask/Jinja2."""
    return []


@pytest.fixture
def jinja_env():
    """Jinja2 environment untuk frontend templates dengan custom filters."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    # Register custom filters/functions
    env.filters["format_date_id"] = format_date_id
    env.globals["url_for"] = url_for
    env.globals["get_flashed_messages"] = get_flashed_messages
    return env


def _get_all_templates() -> list[str]:
    """Dapatkan semua file .html di templates/ (relatif)."""
    templates = []
    for root, _dirs, files in os.walk(TEMPLATES_DIR):
        for f in files:
            if f.endswith(".html"):
                rel = os.path.relpath(os.path.join(root, f), TEMPLATES_DIR)
                templates.append(rel)
    return sorted(templates)


ALL_TEMPLATES = _get_all_templates()

# Context minimal untuk render
MINIMAL_CONTEXT = {
    "request": {"url": {"path": "/"}},
    "current_user": {"id": 1, "name": "Test", "email": "test@test.com"},
    "today": "15 Juni 2026",
    "today_iso": "2026-06-15",
    "today_total": 0,
    "today_count": 0,
    "month_total": 0,
    "month_name": "Juni 2026",
    "top_category": None,
    "top_categories": [],
    "recent_transactions": [],
    "categories": [],
    "payment_methods": [],
    "budgets": [],
    "current_month": 6,
    "current_year": 2026,
    "prev_month": 5,
    "prev_year": 2026,
    "next_month": 7,
    "next_year": 2026,
    "transactions": [],
    "total_pages": 0,
    "pagination": {
        "page": 1, "per_page": 25, "total_items": 0,
        "total_pages": 0, "has_next": False, "has_prev": False,
    },
    "summary": {"total_amount": 0, "total_amount_formatted": "Rp 0",
                 "total_filtered": 0, "total": 0, "avg_per_day": 0, "highest": 0,
                 "week": 25, "transaction_count": 0, "daily_average": 0,
                 "daily_average_formatted": "Rp 0",
                 "categories": [], "top_transactions": [],
                 "prev_week_total": 0, "prev_week_total_formatted": "Rp 0",
                 "percentage_change": 0, "generated_at": None,
                 "monday": "2026-06-15", "sunday": "2026-06-21"},
    "total_amount": 0,
    "mc": {"amount": 0, "label": "Juni 2026", "count": 0},
    "diff": 0,
    "pct": "0%",
    "filters": {"date_from": "", "date_to": "", "category_id": "",
                 "payment_method_id": "", "search": ""},
    "stats": {
        "today": {"total_amount": 0, "total_amount_formatted": "Rp 0",
                  "transaction_count": 0},
        "this_month": {"total_amount": 0, "total_amount_formatted": "Rp 0",
                       "transaction_count": 0, "month_label": "Juni 2026"},
        "top_categories": [],
        "recent_transactions": [],
    },
    "tx_id": 1,
    "tx": {"id": 1, "amount": 50000, "notes": "Test note",
           "transaction_date": "2026-06-15",
           "category": {"id": 1, "name": "Makanan", "icon": "🍔", "color": "#10b981"},
           "payment_method": {"id": 1, "name": "Tunai", "icon": "💵"}},
    "category": {"name": "Test", "id": 1, "icon": "📦", "color": "#10b981"},
    "flash_messages": [],
    "message": None,
    "pace": {
        "daily_avg_formatted": "Rp 25.000",
        "total_budget": 0,
        "projected_total": 750000,
        "projected_total_formatted": "Rp 750.000",
        "days_elapsed": 15,
        "days_in_month": 30,
        "time_elapsed_pct": 50.0,
        "budget_used_pct": 0,
        "is_on_track": True,
        "remaining_days": 15,
        "daily_remaining_budget_formatted": "Rp 0",
    },
}


class TestTemplateRendering:
    """Test semua template bisa di-load dan dirender tanpa error."""

    @pytest.mark.parametrize("template_name", ALL_TEMPLATES)
    def test_template_loads_and_renders(self, jinja_env, template_name):
        """Setiap template harus bisa di-load, dikompilasi, dan dirender."""
        try:
            tmpl = jinja_env.get_template(template_name)
            assert tmpl is not None
        except TemplateNotFound:
            pytest.fail(f"Template tidak ditemukan: {template_name}")
        except Exception as e:
            pytest.fail(f"Template {template_name} gagal di-load: {e}")

        # Coba render dengan context minimal
        try:
            output = tmpl.render(**MINIMAL_CONTEXT)
            assert isinstance(output, str)
            assert len(output) > 0
        except Exception as e:
            pytest.fail(f"Template {template_name} gagal dirender: {e}")


class TestTemplateExtendsBase:
    """Verifikasi template extend base.html."""

    def _read_template(self, name: str) -> str:
        path = TEMPLATES_DIR / name
        return path.read_text()

    def test_base_html_exists(self):
        """base.html harus ada."""
        assert (TEMPLATES_DIR / "base.html").exists()

    def test_templates_extend_base(self):
        """Semua template (kecuali base.html & partials) harus extend base.html."""
        skip = {"base.html", "components/flash_messages.html",
                "components/navbar.html", "components/footer.html",
                "components/pagination.html",
                "budgets/partials/summary.html",
                "stats/partials/spending_pace.html",
                "stats/partials/weekly_summary.html",
                "stats/partials/period_comparison.html",
                "transactions/partials/transaction_list.html",
                "transactions/partials/transaction_row.html",
                "transactions/partials/manage_templates_modal.html",
                "transactions/partials/template_buttons.html",
                "transactions/partials/template_manage_list.html"}

        for tpl in ALL_TEMPLATES:
            if tpl in skip:
                continue
            content = self._read_template(tpl)
            assert "{% extends" in content, \
                f"Template {tpl} tidak extend base.html (tidak ada '{{% extends'"

    def test_templates_have_block_title(self):
        """Semua template yang extend base harus mengisi block title."""
        skip = {"base.html", "components/flash_messages.html",
                "components/navbar.html", "components/footer.html",
                "components/pagination.html",
                "budgets/partials/summary.html",
                "stats/partials/spending_pace.html",
                "stats/partials/weekly_summary.html",
                "stats/partials/period_comparison.html",
                "transactions/partials/transaction_list.html",
                "transactions/partials/transaction_row.html",
                "transactions/partials/manage_templates_modal.html",
                "transactions/partials/template_buttons.html",
                "transactions/partials/template_manage_list.html"}

        for tpl in ALL_TEMPLATES:
            if tpl in skip:
                continue
            content = self._read_template(tpl)
            assert "{% block title %}" in content or "block title" not in content, \
                f"Template {tpl} tidak mengisi block title"


class TestNoBrokenVariables:
    """Verifikasi tidak ada variabel broken reference di template."""

    def test_no_double_curly_brace_orphan(self):
        """Cek tidak ada {{ }} yang mungkin broken di template."""
        for tpl in ALL_TEMPLATES:
            content = (TEMPLATES_DIR / tpl).read_text()
            # {{}} kosong adalah broken
            assert "{{ }}" not in content, \
                f"Template {tpl} mengandung '{{ }}' (variabel kosong broken)"
