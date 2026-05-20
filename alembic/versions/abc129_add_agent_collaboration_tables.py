"""add agent collaboration tables

Revision ID: abc129
Revises: add_alert_phone_tables
Create Date: 2026-05-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc129'
down_revision = '37c25d5c3b8f'
branch_labels = None
depends_on = None


def upgrade():
    # 创建工作流定义表
    op.create_table(
        'agent_workflows',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('version', sa.String(50), nullable=True, server_default='1.0.0'),
        sa.Column('definition', sa.JSON, nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='active', index=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # 创建工作流实例表
    op.create_table(
        'agent_workflow_instances',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workflow_id', sa.String(36), sa.ForeignKey('agent_workflows.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=True, server_default='pending', index=True),
        sa.Column('current_node_id', sa.String(36), nullable=True),
        sa.Column('variables', sa.JSON, nullable=True),
        sa.Column('node_results', sa.JSON, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True, server_default=sa.func.now())
    )
    
    # 创建经验记录表
    op.create_table(
        'agent_experiences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_type', sa.String(100), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('context', sa.JSON, nullable=True),
        sa.Column('result', sa.String(20), nullable=False, index=True),
        sa.Column('reward', sa.Float, nullable=True, server_default='0.0'),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True, server_default=sa.func.now(), index=True)
    )
    
    # 创建协作日志表
    op.create_table(
        'agent_coordination_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), nullable=False, index=True),
        sa.Column('agent_id', sa.String(36), nullable=True, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('duration', sa.Float, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('data', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True, server_default=sa.func.now(), index=True)
    )
    
    # 创建智能体信息表
    op.create_table(
        'agent_infos',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_type', sa.String(100), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=True, server_default='idle', index=True),
        sa.Column('current_task_id', sa.String(36), nullable=True),
        sa.Column('capabilities', sa.JSON, nullable=True),
        sa.Column('completed_tasks', sa.Integer, nullable=True, server_default='0'),
        sa.Column('failed_tasks', sa.Integer, nullable=True, server_default='0'),
        sa.Column('load', sa.Float, nullable=True, server_default='0.0'),
        sa.Column('last_heartbeat', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True, server_default=sa.func.now(), onupdate=sa.func.now())
    )


def downgrade():
    op.drop_table('agent_infos')
    op.drop_table('agent_coordination_logs')
    op.drop_table('agent_experiences')
    op.drop_table('agent_workflow_instances')
    op.drop_table('agent_workflows')
