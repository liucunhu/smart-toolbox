"""add content task fields

Revision ID: abc127
Revises: abc126
Create Date: 2026-05-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc127'
down_revision = 'abc126'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加任务类型字段
    op.add_column('content_tasks', sa.Column('task_type', sa.String(50), nullable=True))
    
    # 添加进度字段
    op.add_column('content_tasks', sa.Column('progress', sa.Integer(), nullable=True, server_default='0'))
    
    # 添加时间戳字段
    op.add_column('content_tasks', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('content_tasks', sa.Column('completed_at', sa.DateTime(), nullable=True))
    
    # 添加错误信息和数据字段
    op.add_column('content_tasks', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('content_tasks', sa.Column('input_data', sa.JSON(), nullable=True))
    op.add_column('content_tasks', sa.Column('output_data', sa.JSON(), nullable=True))
    
    # 更新状态字段的注释，添加cancelled选项
    op.alter_column('content_tasks', 'status', 
                    existing_type=sa.String(20),
                    comment='pending, processing, completed, failed, cancelled')


def downgrade() -> None:
    # 删除添加的字段
    op.drop_column('content_tasks', 'output_data')
    op.drop_column('content_tasks', 'input_data')
    op.drop_column('content_tasks', 'error_message')
    op.drop_column('content_tasks', 'completed_at')
    op.drop_column('content_tasks', 'started_at')
    op.drop_column('content_tasks', 'progress')
    op.drop_column('content_tasks', 'task_type')
