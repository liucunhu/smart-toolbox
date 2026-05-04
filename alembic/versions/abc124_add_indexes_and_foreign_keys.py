"""add indexes and foreign keys
Revision ID: abc124
Revises: abc123
Create Date: 2026-04-30 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc124'
down_revision = 'abc123'
branch_labels = None
depends_on = None


def upgrade():
    """添加索引和外键约束"""
    
    # 为 accounts 表添加索引
    op.create_index('ix_accounts_platform', 'accounts', ['platform'], unique=False)
    op.create_index('ix_accounts_status', 'accounts', ['status'], unique=False)
    op.create_index('ix_accounts_health_score', 'accounts', ['health_score'], unique=False)
    
    # 为 content_tasks 表添加索引
    op.create_index('ix_content_tasks_status', 'content_tasks', ['status'], unique=False)
    op.create_index('ix_content_tasks_target_platform', 'content_tasks', ['target_platform'], unique=False)
    
    # 为 publish_records 表添加索引
    op.create_index('ix_publish_records_account_id', 'publish_records', ['account_id'], unique=False)
    op.create_index('ix_publish_records_content_task_id', 'publish_records', ['content_task_id'], unique=False)
    op.create_index('ix_publish_records_publish_status', 'publish_records', ['publish_status'], unique=False)
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_publish_records_account',
        'publish_records',
        'accounts',
        ['account_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_publish_records_content_task',
        'publish_records',
        'content_tasks',
        ['content_task_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    """回滚索引和外键约束"""
    
    # 删除外键约束
    op.drop_constraint('fk_publish_records_content_task', 'publish_records', type_='foreignkey')
    op.drop_constraint('fk_publish_records_account', 'publish_records', type_='foreignkey')
    
    # 删除索引
    op.drop_index('ix_publish_records_publish_status', table_name='publish_records')
    op.drop_index('ix_publish_records_content_task_id', table_name='publish_records')
    op.drop_index('ix_publish_records_account_id', table_name='publish_records')
    op.drop_index('ix_content_tasks_target_platform', table_name='content_tasks')
    op.drop_index('ix_content_tasks_status', table_name='content_tasks')
    op.drop_index('ix_accounts_health_score', table_name='accounts')
    op.drop_index('ix_accounts_status', table_name='accounts')
    op.drop_index('ix_accounts_platform', table_name='accounts')
