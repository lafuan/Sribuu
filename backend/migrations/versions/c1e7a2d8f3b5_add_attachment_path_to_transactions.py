"""add attachment_path to transactions table

Revision ID: c1e7a2d8f3b5
Revises: c6b2e9a3d0f4
Create Date: 2026-06-22 09:00:00.000000+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1e7a2d8f3b5"
down_revision: Union[str, None] = "c6b2e9a3d0f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("attachment_path", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transactions", "attachment_path")
