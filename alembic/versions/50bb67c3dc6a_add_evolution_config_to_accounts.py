"""add_evolution_config_to_accounts

Revision ID: 50bb67c3dc6a
Revises: 5c7d0dd6eb8b
Create Date: 2026-05-12 16:10:42.112869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50bb67c3dc6a'
down_revision: Union[str, Sequence[str], None] = '5c7d0dd6eb8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加进化配置字段
    op.add_column('accounts', sa.Column('evolution_config', sa.JSON(), nullable=True))
    op.add_column('accounts', sa.Column('last_evolution_time', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # 删除进化配置字段
    op.drop_column('accounts', 'last_evolution_time')
    op.drop_column('accounts', 'evolution_config')
