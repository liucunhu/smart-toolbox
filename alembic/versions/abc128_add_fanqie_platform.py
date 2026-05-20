"""Alembic migration for adding Fanqie (Tomato Novel) platform support

Revision ID: fanqie_platform_support
Revises: abc127
Create Date: 2026-05-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fanqie_platform_support'
down_revision = 'abc127'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MySQL: 修改enum类型添加新值
    op.execute("ALTER TABLE accounts MODIFY COLUMN platform ENUM('douyin', 'xiaohongshu', 'bilibili', 'video_account', 'toutiao', 'fanqie') NOT NULL")
    op.execute("ALTER TABLE content_tasks MODIFY COLUMN target_platform ENUM('douyin', 'xiaohongshu', 'bilibili', 'video_account', 'toutiao', 'fanqie')")
    
    # Add Fanqie-specific fields to accounts table
    op.add_column('accounts', sa.Column('novel_id', sa.String(100), nullable=True))
    op.add_column('accounts', sa.Column('novel_title', sa.String(500), nullable=True))
    op.add_column('accounts', sa.Column('novel_status', sa.String(20), nullable=True))
    op.add_column('accounts', sa.Column('writer_cookies', sa.Text(), nullable=True))
    op.add_column('accounts', sa.Column('writer_token', sa.String(500), nullable=True))
    op.add_column('accounts', sa.Column('total_chapters', sa.Integer(), server_default='0'))
    op.add_column('accounts', sa.Column('total_words', sa.Integer(), server_default='0'))
    op.add_column('accounts', sa.Column('total_readers', sa.Integer(), server_default='0'))
    op.add_column('accounts', sa.Column('avg_completion_rate', sa.Float(), server_default='0.0'))
    op.add_column('accounts', sa.Column('daily_income', sa.Float(), server_default='0.0'))
    op.add_column('accounts', sa.Column('monthly_income', sa.Float(), server_default='0.0'))
    op.add_column('accounts', sa.Column('total_income', sa.Float(), server_default='0.0'))
    op.add_column('accounts', sa.Column('consecutive_days', sa.Integer(), server_default='0'))
    op.add_column('accounts', sa.Column('last_update_date', sa.DateTime(), nullable=True))
    op.add_column('accounts', sa.Column('qualification_for_bonus', sa.Boolean(), server_default='0'))
    
    # Create novels table
    op.create_table(
        'novels',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounts.id'), index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('subtitle', sa.String(500), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('cover_image_path', sa.String(500), nullable=True),
        sa.Column('introduction', sa.Text(), nullable=True),
        sa.Column('golden_three_chapters', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('publish_schedule', sa.JSON(), nullable=True),
        sa.Column('total_chapters', sa.Integer(), server_default='0'),
        sa.Column('total_words', sa.Integer(), server_default='0'),
        sa.Column('total_reads', sa.Integer(), server_default='0'),
        sa.Column('total_favorites', sa.Integer(), server_default='0'),
        sa.Column('avg_rating', sa.Float(), server_default='0.0'),
        sa.Column('evolution_config', sa.JSON(), nullable=True),
        sa.Column('last_evolution_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create chapters table
    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('novel_id', sa.Integer(), sa.ForeignKey('novels.id'), index=True),
        sa.Column('chapter_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('scheduled_time', sa.DateTime(), nullable=True),
        sa.Column('published_time', sa.DateTime(), nullable=True),
        sa.Column('platform_chapter_id', sa.String(100), nullable=True),
        sa.Column('read_count', sa.Integer(), server_default='0'),
        sa.Column('completion_rate', sa.Float(), server_default='0.0'),
        sa.Column('retention_rate', sa.Float(), server_default='0.0'),
        sa.Column('ai_generated_ratio', sa.Float(), server_default='0.0'),
        sa.Column('manual_revision_notes', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create fanqie_analytics table
    op.create_table(
        'fanqie_analytics',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('novel_id', sa.Integer(), sa.ForeignKey('novels.id'), index=True),
        sa.Column('chapter_id', sa.Integer(), sa.ForeignKey('chapters.id'), index=True, nullable=True),
        sa.Column('stat_date', sa.DateTime(), nullable=False, index=True),
        sa.Column('daily_reads', sa.Integer(), server_default='0'),
        sa.Column('new_followers', sa.Integer(), server_default='0'),
        sa.Column('new_favorites', sa.Integer(), server_default='0'),
        sa.Column('comments_count', sa.Integer(), server_default='0'),
        sa.Column('daily_ad_revenue', sa.Float(), server_default='0.0'),
        sa.Column('reading_minutes', sa.Integer(), server_default='0'),
        sa.Column('avg_reading_time', sa.Float(), server_default='0.0'),
        sa.Column('completion_rate', sa.Float(), server_default='0.0'),
        sa.Column('retention_rate_day1', sa.Float(), server_default='0.0'),
        sa.Column('retention_rate_day7', sa.Float(), server_default='0.0'),
        sa.Column('category_rank', sa.Integer(), nullable=True),
        sa.Column('overall_rank', sa.Integer(), nullable=True),
        sa.Column('rising_rank', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('fanqie_analytics')
    op.drop_table('chapters')
    op.drop_table('novels')
    
    # Remove Fanqie-specific fields from accounts table
    op.drop_column('accounts', 'qualification_for_bonus')
    op.drop_column('accounts', 'last_update_date')
    op.drop_column('accounts', 'consecutive_days')
    op.drop_column('accounts', 'total_income')
    op.drop_column('accounts', 'monthly_income')
    op.drop_column('accounts', 'daily_income')
    op.drop_column('accounts', 'avg_completion_rate')
    op.drop_column('accounts', 'total_readers')
    op.drop_column('accounts', 'total_words')
    op.drop_column('accounts', 'total_chapters')
    op.drop_column('accounts', 'writer_token')
    op.drop_column('accounts', 'writer_cookies')
    op.drop_column('accounts', 'novel_status')
    op.drop_column('accounts', 'novel_title')
    op.drop_column('accounts', 'novel_id')
