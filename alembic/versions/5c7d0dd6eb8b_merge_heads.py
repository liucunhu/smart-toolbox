"""merge_heads

Revision ID: 5c7d0dd6eb8b
Revises: abc124, create_users_table, abc125, abc127
Create Date: 2026-05-12 16:10:35.118638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c7d0dd6eb8b'
down_revision: Union[str, Sequence[str], None] = ('abc124', 'create_users_table', 'abc125', 'abc127')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
