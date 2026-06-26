"""add parent_transaction_id for split transactions

Revision ID: b4a7f2e9c8d1
Revises: c1e7a2d8f3b5
Create Date: 2026-06-26 09:00:00.000000+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4a7f2e9c8d1"
down_revision: Union[str, None] = "c1e7a2d8f3b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("parent_transaction_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_parent",
        "transactions", "transactions",
        ["parent_transaction_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "idx_tx_parent", "transactions", ["parent_transaction_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_tx_parent", table_name="transactions")
    op.drop_constraint("fk_transactions_parent", "transactions", type_="foreignkey")
    op.drop_column("transactions", "parent_transaction_id")
