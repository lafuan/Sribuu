"""add notification preferences to users table

Revision ID: c6b2e9a3d0f4
Revises: 0c530f594843
Create Date: 2026-06-20 19:00:00.000000+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6b2e9a3d0f4'
down_revision: Union[str, None] = '0c530f594843'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('notification_enabled', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('reminder_time', sa.String(length=5), nullable=True, server_default='20:00'))


def downgrade() -> None:
    op.drop_column('users', 'reminder_time')
    op.drop_column('users', 'notification_enabled')
