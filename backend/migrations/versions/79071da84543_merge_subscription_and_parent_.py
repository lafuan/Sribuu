"""merge subscription and parent_transaction_id

Revision ID: 79071da84543
Revises: b4a7f2e9c8d1, f7e3d8a2b1c4
Create Date: 2026-06-27 08:09:21.811439+07:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79071da84543'
down_revision: Union[str, None] = ('b4a7f2e9c8d1', 'f7e3d8a2b1c4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
