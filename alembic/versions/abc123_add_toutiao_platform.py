"""Add toutiao platform support and article fields

Revision ID: abc123
Revises: 
Create Date: 2026-04-29 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加头条平台枚举（MySQL 需要修改枚举类型）
    op.execute("ALTER TABLE accounts MODIFY platform ENUM('douyin', 'xiaohongshu', 'bilibili', 'video_account', 'toutiao') NOT NULL")
    op.execute("ALTER TABLE content_tasks MODIFY target_platform ENUM('douyin', 'xiaohongshu', 'bilibili', 'video_account', 'toutiao')")
    
    # 2. 添加头条文章字段
    op.add_column('content_tasks', sa.Column('article_title', sa.String(500), nullable=True))
    op.add_column('content_tasks', sa.Column('article_content', sa.Text, nullable=True))
    op.add_column('content_tasks', sa.Column('article_category', sa.String(100), nullable=True))
    op.add_column('content_tasks', sa.Column('tags', sa.JSON, nullable=True))
    
    # 3. 添加头条账号字段
    op.add_column('accounts', sa.Column('cookies', sa.Text, nullable=True))
    op.add_column('accounts', sa.Column('session_token', sa.String(500), nullable=True))
    op.add_column('accounts', sa.Column('publish_url', sa.String(500), nullable=True))


def downgrade():
    # 回滚操作
    op.drop_column('accounts', 'publish_url')
    op.drop_column('accounts', 'session_token')
    op.drop_column('accounts', 'cookies')
    
    op.drop_column('content_tasks', 'tags')
    op.drop_column('content_tasks', 'article_category')
    op.drop_column('content_tasks', 'article_content')
    op.drop_column('content_tasks', 'article_title')
    
    op.execute("ALTER TABLE accounts MODIFY platform ENUM('douyin', 'xiaohongshu', 'bilibili', 'video_account') NOT NULL")
    op.execute("ALTER TABLE content_tasks MODIFY target_platform ENUM('douyin', 'xiaohongshu', 'bilibili', 'video_account')")
