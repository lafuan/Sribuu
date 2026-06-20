"""
SQLAlchemy models untuk Sribuu.
"""

from datetime import datetime

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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(128), nullable=False)
    notification_enabled = Column(Integer, nullable=False, default=0)
    reminder_time = Column(String(5), nullable=True, default="20:00")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

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
    amount = Column(Integer, nullable=False)  # dalam Rupiah (integer)
    notes = Column(Text, nullable=True)
    transaction_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    payment_method = relationship("PaymentMethod", back_populates="transactions")


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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")
