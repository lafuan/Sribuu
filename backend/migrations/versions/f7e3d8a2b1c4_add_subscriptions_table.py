"""add subscriptions table

Revision ID: f7e3d8a2b1c4
Revises: a1b2c3d4e5f6
Create Date: 2026-06-27 10:00:00.000000+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7e3d8a2b1c4'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('frequency', sa.String(length=10), nullable=False, server_default='monthly'),
    sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
    sa.Column('occurrence_count', sa.Integer(), nullable=False, server_default='1'),
    sa.Column('last_detected_date', sa.Date(), nullable=True),
    sa.Column('first_detected_date', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_subscriptions_user_active', 'subscriptions', ['user_id', 'is_active'], unique=False)
    op.create_index('idx_subscriptions_user_category', 'subscriptions', ['user_id', 'category_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_subscriptions_user_category', table_name='subscriptions')
    op.drop_index('idx_subscriptions_user_active', table_name='subscriptions')
    op.drop_table('subscriptions')
