"""
SQLAlchemy models untuk Sribuu.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..database import Base


def _utc_now() -> datetime:
    """Return current UTC datetime as naive (no tzinfo).
    
    asyncpg expects timezone-naive datetimes for TIMESTAMP WITHOUT TIME ZONE columns.
    Using timezone-aware datetimes causes: "can't subtract offset-naive and offset-aware datetimes"
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(128), nullable=False)
    notification_enabled = Column(Integer, nullable=False, default=0)
    reminder_time = Column(String(5), nullable=True, default="20:00")
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        # nama unik per user (kategori user) — kategori default punya user_id NULL
        Index("idx_categories_user_active", "user_id", "is_active"),
        Index("idx_categories_default_active", "is_default", "is_active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(5), nullable=False, default="📦")
    color = Column(String(7), nullable=False, default="#6b7280")
    is_default = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=_utc_now)

    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category", cascade="all, delete-orphan")


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        Index("idx_payment_methods_active", "is_active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False, unique=True)
    icon = Column(String(5), nullable=False, default="💵")
    is_default = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=_utc_now)

    transactions = relationship("Transaction", back_populates="payment_method")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transaction_amount_positive"),
        # Index untuk query utama
        Index("idx_tx_user_date", "user_id", "transaction_date"),
        Index("idx_tx_user_category", "user_id", "category_id"),
        Index("idx_tx_user_payment", "user_id", "payment_method_id"),
        Index("idx_tx_user_amount", "user_id", "transaction_date", "amount"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)
    parent_transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True)
    amount = Column(Integer, nullable=False)  # dalam Rupiah (integer)
    notes = Column(Text, nullable=True)
    attachment_path = Column(String(255), nullable=True)
    transaction_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    payment_method = relationship("PaymentMethod", back_populates="transactions")
    parent = relationship("Transaction", remote_side=[id], backref="children")


class TransactionTemplate(Base):
    """Template transaksi yang sering dipakai (Favorit Transaksi)."""
    __tablename__ = "transaction_templates"
    __table_args__ = (
        Index("idx_templates_user", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Integer, nullable=False)  # dalam Rupiah (integer)
    notes = Column(Text, nullable=True)
    label = Column(String(50), nullable=False)  # Nama label tombol, misal "Makan Siang"
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="transaction_templates")
    category = relationship("Category")
    payment_method = relationship("PaymentMethod")


class WeeklySummary(Base):
    """Cache ringkasan mingguan."""
    __tablename__ = "weekly_summaries"
    __table_args__ = (
        Index("idx_weekly_user_week", "user_id", "year", "week", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)  # 1-53 (ISO week)
    total_amount = Column(Integer, nullable=False, default=0)
    transaction_count = Column(Integer, nullable=False, default=0)
    daily_average = Column(Integer, nullable=False, default=0)
    category_breakdown = Column(Text, nullable=True)  # JSON string: [{cat_id, name, icon, color, total}]
    top_transactions = Column(Text, nullable=True)    # JSON string: [{amount, notes, category_name, date}]
    prev_week_total = Column(Integer, nullable=False, default=0)
    percentage_change = Column(Integer, nullable=False, default=0)  # dalam % (0 = no prev data)
    generated_at = Column(DateTime, nullable=False, default=_utc_now)

    user = relationship("User", backref="weekly_summaries")


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        # Satu budget per kategori per bulan
        Index("idx_budget_user_category_month", "user_id", "category_id", "month", "year", unique=True),
        Index("idx_budget_user_month", "user_id", "month", "year"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)  # dalam Rupiah (integer)
    rollover = Column(Integer, nullable=False, default=0)  # sisa budget bulan lalu
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")


class Bill(Base):
    """Tagihan rutin (listrik, air, internet, dsb)."""
    __tablename__ = "bills"
    __table_args__ = (
        Index("idx_bills_user_due", "user_id", "due_date"),
        Index("idx_bills_user_paid", "user_id", "is_paid"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(100), nullable=False)
    amount = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    frequency = Column(String(10), nullable=False, default="monthly")
    is_paid = Column(Integer, nullable=False, default=0)
    paid_transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="bills")
    category = relationship("Category")
    paid_transaction = relationship("Transaction", foreign_keys=[paid_transaction_id])


class Subscription(Base):
    """Subscription/layanan berulang yang terdeteksi otomatis dari transaksi."""
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("idx_subscriptions_user_active", "user_id", "is_active"),
        Index("idx_subscriptions_user_category", "user_id", "category_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(100), nullable=False)
    amount = Column(Integer, nullable=False)
    frequency = Column(String(10), nullable=False, default="monthly")
    is_active = Column(Integer, nullable=False, default=1)
    occurrence_count = Column(Integer, nullable=False, default=1)
    last_detected_date = Column(Date, nullable=True)
    first_detected_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="subscriptions")
    category = relationship("Category")


class Rule(Base):
    """Auto-categorization rule: IF notes match keyword THEN assign category."""
    __tablename__ = "rules"
    __table_args__ = (
        Index("idx_rules_user_active", "user_id", "is_active"),
        Index("idx_rules_user_priority", "user_id", "priority"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    match_keywords = Column(String(500), nullable=False)  # comma-separated keywords
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    match_mode = Column(String(20), nullable=False, default="contains")  # contains, exact, startswith
    is_active = Column(Integer, nullable=False, default=1)
    priority = Column(Integer, nullable=False, default=0)
    match_count = Column(Integer, nullable=False, default=0)
    last_matched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    updated_at = Column(DateTime, nullable=False, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="rules")
    category = relationship("Category")
