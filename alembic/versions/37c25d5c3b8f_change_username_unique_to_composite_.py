"""change_username_unique_to_composite_index

Revision ID: 37c25d5c3b8f
Revises: 3f7c352578ea
Create Date: 2026-05-14 16:54:16.823449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37c25d5c3b8f'
down_revision: Union[str, Sequence[str], None] = '3f7c352578ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 删除旧的单一字段唯一索引
    op.drop_index('ix_accounts_username', table_name='accounts')
    
    # 2. 创建新的联合唯一索引 (platform, username)
    op.create_index('ix_platform_username', 'accounts', ['platform', 'username'], unique=True)
    
    # 3. 保留普通的 username 索引（用于快速查询）
    op.create_index('ix_accounts_username', 'accounts', ['username'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. 删除新的联合唯一索引
    op.drop_index('ix_platform_username', table_name='accounts')
    
    # 2. 删除普通的 username 索引
    op.drop_index('ix_accounts_username', table_name='accounts')
    
    # 3. 恢复旧的唯一索引
    op.create_index('ix_accounts_username', 'accounts', ['username'], unique=True)
