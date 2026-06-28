"""add_rules_table

Revision ID: d68b70c94166
Revises: 3e95af58886f
Create Date: 2026-06-28 17:24:02.111407+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd68b70c94166'
down_revision: Union[str, None] = '3e95af58886f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('rules',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('match_keywords', sa.String(length=500), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('match_mode', sa.String(length=20), nullable=False),
    sa.Column('is_active', sa.Integer(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('match_count', sa.Integer(), nullable=False),
    sa.Column('last_matched_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rules_user_active', 'rules', ['user_id', 'is_active'], unique=False)
    op.create_index('idx_rules_user_priority', 'rules', ['user_id', 'priority'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_rules_user_priority', table_name='rules')
    op.drop_index('idx_rules_user_active', table_name='rules')
    op.drop_table('rules')
