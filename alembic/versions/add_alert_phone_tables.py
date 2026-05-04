"""add alert and phone record tables

Revision ID: add_alert_phone_tables
Revises: 
Create Date: 2026-05-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_alert_phone_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""
    # 创建报警记录表
    op.create_table(
        'alert_records',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('status', sa.String(20), server_default='success'),
        sa.Column('channels', sa.String(200)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # 创建手机号使用记录表
    op.create_table(
        'phone_records',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('phone_number', sa.String(20), nullable=False, index=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), server_default='in_use'),
        sa.Column('verification_code', sa.String(10)),
        sa.Column('used_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('released_at', sa.DateTime())
    )


def downgrade() -> None:
    """降级数据库结构"""
    op.drop_table('phone_records')
    op.drop_table('alert_records')
