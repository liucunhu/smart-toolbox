"""add_nurturing_and_health_models

Revision ID: abc125
Revises: add_alert_phone_tables
Create Date: 2026-05-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc125'
down_revision = 'add_alert_phone_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""
    
    # 创建养号会话表
    op.create_table(
        'nurturing_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('session_start', sa.DateTime(), nullable=True),
        sa.Column('session_end', sa.DateTime(), nullable=True),
        sa.Column('videos_watched', sa.Integer(), nullable=False, default=0),
        sa.Column('watch_duration', sa.Integer(), nullable=False, default=0),
        sa.Column('likes_count', sa.Integer(), nullable=False, default=0),
        sa.Column('comments_count', sa.Integer(), nullable=False, default=0),
        sa.Column('forwards_count', sa.Integer(), nullable=False, default=0),
        sa.Column('follows_count', sa.Integer(), nullable=False, default=0),
        sa.Column('collects_count', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(50), nullable=False, default='in_progress'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建账号健康指标表
    op.create_table(
        'account_health_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('health_score', sa.Float(), nullable=False, default=50.0),
        sa.Column('activity_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('interaction_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('content_quality_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('risk_level', sa.String(20), nullable=False, default='low'),
        sa.Column('last_nurtured_at', sa.DateTime(), nullable=True),
        sa.Column('total_nurturing_sessions', sa.Integer(), nullable=False, default=0),
        sa.Column('total_watch_time', sa.Integer(), nullable=False, default=0),
        sa.Column('total_interactions', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id')
    )
    
    # 为accounts表添加health_score字段（如果不存在）
    try:
        op.add_column('accounts', sa.Column('health_score', sa.Float(), nullable=True, server_default='50.0'))
    except Exception:
        pass  # 字段可能已存在
    
    # 创建索引
    op.create_index('ix_nurturing_sessions_account_id', 'nurturing_sessions', ['account_id'])
    op.create_index('ix_nurturing_sessions_platform', 'nurturing_sessions', ['platform'])
    op.create_index('ix_nurturing_sessions_status', 'nurturing_sessions', ['status'])
    op.create_index('ix_account_health_metrics_account_id', 'account_health_metrics', ['account_id'])


def downgrade() -> None:
    """降级数据库结构"""
    
    # 删除索引
    op.drop_index('ix_account_health_metrics_account_id', table_name='account_health_metrics')
    op.drop_index('ix_nurturing_sessions_status', table_name='nurturing_sessions')
    op.drop_index('ix_nurturing_sessions_platform', table_name='nurturing_sessions')
    op.drop_index('ix_nurturing_sessions_account_id', table_name='nurturing_sessions')
    
    # 删除表
    op.drop_table('account_health_metrics')
    op.drop_table('nurturing_sessions')
    
    # 删除accounts表的health_score字段
    try:
        op.drop_column('accounts', 'health_score')
    except Exception:
        pass  # 字段可能不存在
