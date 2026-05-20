"""Merge fanqie and alert branches

Revision ID: 451c9bdb73e1
Revises: 50bb67c3dc6a, fanqie_platform_support
Create Date: 2026-05-14 14:47:08.388461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '451c9bdb73e1'
down_revision: Union[str, Sequence[str], None] = ('50bb67c3dc6a', 'fanqie_platform_support')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
