"""add_llm_config_tables

Revision ID: abc126
Revises: add_alert_phone_tables
Create Date: 2026-05-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc126'
down_revision = 'add_alert_phone_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 添加LLM配置表和系统配置表"""
    
    # 创建大模型提供商枚举类型
    llm_provider_enum = sa.Enum('siliconflow', 'modelscope', 'dashscope', 'deepseek', 'openai', name='llmproviderenum')
    llm_provider_enum.create(op.get_bind(), checkfirst=True)
    
    # 创建功能类型枚举类型
    function_type_enum = sa.Enum('copywriting', 'cover_generation', 'image_generation', 'content_analysis', name='functiontypeenum')
    function_type_enum.create(op.get_bind(), checkfirst=True)
    
    # 创建 llm_configs 表
    op.create_table(
        'llm_configs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('provider', llm_provider_enum, nullable=False, index=True),
        sa.Column('function_type', function_type_enum, nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('api_key', sa.String(500)),
        sa.Column('base_url', sa.String(500)),
        sa.Column('model_name', sa.String(200), nullable=False),
        sa.Column('image_model_name', sa.String(200)),
        sa.Column('timeout', sa.Integer(), default=60),
        sa.Column('max_tokens', sa.Integer(), default=4096),
        sa.Column('temperature', sa.Float(), default=0.7),
        sa.Column('extra_params', sa.JSON()),
        sa.Column('is_default', sa.Boolean(), default=False, index=True),
        sa.Column('is_active', sa.Boolean(), default=True, index=True),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('description', sa.Text()),
        sa.Column('last_test_time', sa.DateTime()),
        sa.Column('last_test_status', sa.String(20)),
        sa.Column('last_test_error', sa.Text()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 创建索引
    op.create_index('idx_provider_function', 'llm_configs', ['provider', 'function_type'])
    op.create_index('idx_is_default', 'llm_configs', ['is_default'])
    
    # 创建 system_configs 表
    op.create_table(
        'system_configs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('config_key', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('config_value', sa.Text()),
        sa.Column('value_type', sa.String(20), default='string'),
        sa.Column('description', sa.Text()),
        sa.Column('is_encrypted', sa.Boolean(), default=False),
        sa.Column('is_required', sa.Boolean(), default=False),
        sa.Column('default_value', sa.Text()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # 创建索引
    op.create_index('idx_config_category', 'system_configs', ['category'])
    op.create_index('idx_config_key', 'system_configs', ['config_key'], unique=True)


def downgrade() -> None:
    """降级数据库结构 - 删除LLM配置表和系统配置表"""
    
    # 删除索引
    op.drop_index('idx_config_key', table_name='system_configs')
    op.drop_index('idx_config_category', table_name='system_configs')
    op.drop_index('idx_is_default', table_name='llm_configs')
    op.drop_index('idx_provider_function', table_name='llm_configs')
    
    # 删除表
    op.drop_table('system_configs')
    op.drop_table('llm_configs')
    
    # 删除枚举类型
    function_type_enum = sa.Enum(name='functiontypeenum')
    function_type_enum.drop(op.get_bind(), checkfirst=True)
    
    llm_provider_enum = sa.Enum(name='llmproviderenum')
    llm_provider_enum.drop(op.get_bind(), checkfirst=True)
