"""add bills table

Revision ID: a1b2c3d4e5f6
Revises: c1e7a2d8f3b5
Create Date: 2026-06-26 10:00:00.000000+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c1e7a2d8f3b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('bills',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('frequency', sa.String(length=10), nullable=False, server_default='monthly'),
    sa.Column('is_paid', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('paid_transaction_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['paid_transaction_id'], ['transactions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bills_user_due', 'bills', ['user_id', 'due_date'], unique=False)
    op.create_index('idx_bills_user_paid', 'bills', ['user_id', 'is_paid'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_bills_user_paid', table_name='bills')
    op.drop_index('idx_bills_user_due', table_name='bills')
    op.drop_table('bills')
