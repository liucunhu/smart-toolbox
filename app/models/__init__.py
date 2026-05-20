from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, Enum, Index, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

class PlatformEnum(str, enum.Enum):
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    BILIBILI = "bilibili"
    VIDEO_ACCOUNT = "video_account"  # 视频号
    TOUTIAO = "toutiao"  # 今日头条
    FANQIE = "fanqie"  # 番茄小说

class AccountStatusEnum(str, enum.Enum):
    REGISTERING = "registering"
    NURTURING = "nurturing"
    ACTIVE = "active"
    BANNED = "banned"

class Account(Base):
    """账号信息表"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(Enum(PlatformEnum, values_callable=lambda x: [e.value for e in x]), nullable=False)
    username = Column(String(100), index=True)  # 移除 unique=True，使用联合唯一索引
    password = Column(String(255))
    status = Column(Enum(AccountStatusEnum, values_callable=lambda x: [e.value for e in x]), default=AccountStatusEnum.REGISTERING)
    health_score = Column(Float, default=100.0)
    
    # 设备指纹与代理信息 (JSON 存储)
    fingerprint = Column(JSON)
    proxy_ip = Column(String(50))
    
    # 头条账号特有字段
    cookies = Column(Text)  # 登录后的 Cookie（用于自动化发布）
    session_token = Column(String(500))  # 会话令牌
    publish_url = Column(String(500))  # 发布页面 URL
    
    # 番茄小说特有字段
    novel_id = Column(String(100))  # 小说ID（每本书的唯一标识）
    novel_title = Column(String(500))  # 小说标题
    novel_status = Column(String(20))  # 小说状态：ongoing/completed/paused
    writer_cookies = Column(Text)  # 作家专区Cookie
    writer_token = Column(String(500))  # 作家认证Token
    total_chapters = Column(Integer, default=0)  # 总章节数
    total_words = Column(Integer, default=0)  # 总字数
    total_readers = Column(Integer, default=0)  # 累计读者数
    avg_completion_rate = Column(Float, default=0.0)  # 平均读完率
    daily_income = Column(Float, default=0.0)  # 当日收益
    monthly_income = Column(Float, default=0.0)  # 当月收益
    total_income = Column(Float, default=0.0)  # 累计收益
    consecutive_days = Column(Integer, default=0)  # 连续更新天数
    last_update_date = Column(DateTime)  # 最后更新日期
    qualification_for_bonus = Column(Boolean, default=False)  # 是否获得全勤奖资格
    
    # 头条账号特有字段
    toutiao_last_publish_time = Column(DateTime)  # 最后发布时间
    toutiao_consecutive_days = Column(Integer, default=0)  # 连续发文天数
    toutiao_qualification_for_bonus = Column(Boolean, default=False)  # 收益资格
    
    # 自适应进化配置（JSON存储）
    evolution_config = Column(JSON)  # 进化策略配置
    last_evolution_time = Column(DateTime)  # 最后一次进化时间
    
    # 关联关系
    nurturing_sessions = relationship("NurturingSession", back_populates="account", cascade="all, delete-orphan")
    health_metrics = relationship("AccountHealthMetrics", back_populates="account", uselist=False, cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 联合唯一索引：同一平台下用户名唯一
    __table_args__ = (
        Index('ix_platform_username', 'platform', 'username', unique=True),
    )


class Novel(Base):
    """小说基本信息表"""
    __tablename__ = "novels"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), index=True)  # 关联账号
    
    # 基本信息
    title = Column(String(500), nullable=False)  # 小说标题
    subtitle = Column(String(500))  # 副标题/简介
    category = Column(String(50))  # 分类：都市/玄幻/仙侠/历史等
    tags = Column(JSON)  # 标签列表
    
    # 封面和介绍
    cover_image_path = Column(String(500))  # 封面图路径
    introduction = Column(Text)  # 小说简介
    golden_three_chapters = Column(Text)  # 黄金三章内容（用于审核）
    
    # 状态管理
    status = Column(String(20), default="draft")  # draft/published/ongoing/completed
    publish_schedule = Column(JSON)  # 发布计划（定时发布配置）
    
    # 统计数据
    total_chapters = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    total_reads = Column(Integer, default=0)
    total_favorites = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)  # 平均评分
    
    # 进化配置（自适应优化）
    evolution_config = Column(JSON)  # 内容进化策略
    last_evolution_time = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    account = relationship("Account", backref="novels")
    chapters = relationship("Chapter", back_populates="novel", cascade="all, delete-orphan")


class Chapter(Base):
    """章节信息表"""
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey('novels.id'), index=True)
    
    # 章节信息
    chapter_number = Column(Integer, nullable=False)  # 章节序号
    title = Column(String(500), nullable=False)  # 章节标题
    content = Column(Text, nullable=False)  # 章节内容
    word_count = Column(Integer, default=0)  # 字数统计
    
    # 发布状态
    status = Column(String(20), default="draft")  # draft/scheduled/published/failed
    scheduled_time = Column(DateTime)  # 计划发布时间
    published_time = Column(DateTime)  # 实际发布时间
    platform_chapter_id = Column(String(100))  # 平台上的章节ID
    
    # 数据表现
    read_count = Column(Integer, default=0)  # 阅读人数
    completion_rate = Column(Float, default=0.0)  # 读完率
    retention_rate = Column(Float, default=0.0)  # 留存率（有多少人继续读下一章）
    
    # AI辅助标记
    ai_generated_ratio = Column(Float, default=0.0)  # AI生成比例（0-1）
    manual_revision_notes = Column(Text)  # 人工修改备注
    
    error_message = Column(Text)  # 发布错误信息
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    novel = relationship("Novel", back_populates="chapters")


class FanqieAnalytics(Base):
    """番茄小说数据分析表"""
    __tablename__ = "fanqie_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey('novels.id'), index=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'), index=True, nullable=True)
    
    # 日期维度
    stat_date = Column(DateTime, nullable=False, index=True)
    
    # 阅读数据
    daily_reads = Column(Integer, default=0)  # 日阅读量
    new_followers = Column(Integer, default=0)  # 新增关注
    new_favorites = Column(Integer, default=0)  # 新增书架
    comments_count = Column(Integer, default=0)  # 评论数
    
    # 收益数据
    daily_ad_revenue = Column(Float, default=0.0)  # 广告收益
    reading_minutes = Column(Integer, default=0)  # 总阅读时长（分钟）
    avg_reading_time = Column(Float, default=0.0)  # 平均阅读时长
    
    # 质量指标
    completion_rate = Column(Float, default=0.0)  # 读完率
    retention_rate_day1 = Column(Float, default=0.0)  # 次日留存
    retention_rate_day7 = Column(Float, default=0.0)  # 7日留存
    
    # 排名数据
    category_rank = Column(Integer)  # 分类排名
    overall_rank = Column(Integer)  # 总榜排名
    rising_rank = Column(Integer)  # 上升榜排名
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    novel = relationship("Novel", backref="analytics")
    chapter = relationship("Chapter", backref="analytics", uselist=False)


class Article(Base):
    """头条文章表"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), index=True)
    
    # 基本信息
    title = Column(String(500), nullable=False)
    content = Column(Text)
    category = Column(String(50))
    tags = Column(JSON)
    cover_image_path = Column(String(500))
    
    # 发布状态
    status = Column(String(20), default='draft')  # draft/scheduled/published/failed
    scheduled_publish_time = Column(DateTime)
    published_time = Column(DateTime)
    platform_article_id = Column(String(100))
    
    # 性能指标
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    
    # A/B测试
    ab_test_id = Column(String(100))
    variant_id = Column(String(50))
    
    # 错误信息
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    account = relationship("Account", backref="articles")

class ContentTask(Base):
    """内容创作任务表"""
    __tablename__ = "content_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), unique=True, index=True)  # UUID
    original_topic = Column(Text)
    target_platform = Column(Enum(PlatformEnum, values_callable=lambda x: [e.value for e in x]))
    
    # 任务类型
    task_type = Column(String(50))  # generate_script, process_video, generate_cover, compliance_check, publish, ai_cover, template_cover
    
    # 生成结果存储路径（视频类内容）
    script_path = Column(String(255))
    video_path = Column(String(255))
    cover_path = Column(String(255))
    
    # 头条文章特有字段
    article_title = Column(String(500))  # 文章标题
    article_content = Column(Text)  # 文章正文
    article_category = Column(String(100))  # 文章分类
    tags = Column(JSON)  # 标签列表
    
    # 任务状态和进度
    status = Column(String(20), default="pending")  # pending, processing, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 进度百分比 0-100
    
    # 时间戳
    started_at = Column(DateTime)  # 开始时间
    completed_at = Column(DateTime)  # 完成时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 错误信息和数据
    error_message = Column(Text)  # 错误信息
    input_data = Column(JSON)  # 输入数据
    output_data = Column(JSON)  # 输出数据

class PublishRecord(Base):
    """分发记录表"""
    __tablename__ = "publish_records"
    
    # 复合索引优化查询性能
    __table_args__ = (
        Index('idx_publish_status_time', 'publish_status', 'publish_time'),
        Index('idx_created_at', 'created_at'),
        Index('idx_account_content', 'account_id', 'content_task_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, index=True)
    content_task_id = Column(Integer, index=True)
    
    publish_status = Column(String(20), default="scheduled", index=True) # scheduled, published, failed
    publish_time = Column(DateTime, index=True)
    platform_url = Column(String(500)) # 发布后的链接
    
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AlertRecord(Base):
    """报警记录表"""
    __tablename__ = "alert_records"
    
    # 索引优化
    __table_args__ = (
        Index('idx_alert_type_status', 'type', 'status'),
        Index('idx_alert_created', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, index=True)  # account_anomaly, task_failed, system_health
    subject = Column(String(200), nullable=False)  # 报警主题
    message = Column(Text)  # 报警详细内容
    status = Column(String(20), default="success", index=True)  # success, failed
    channels = Column(String(200))  # 发送渠道，逗号分隔（email,dingtalk）
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PhoneRecord(Base):
    """手机号使用记录表"""
    __tablename__ = "phone_records"
    
    # 索引优化
    __table_args__ = (
        Index('idx_phone_platform', 'phone_number', 'platform'),
        Index('idx_phone_status', 'status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)  # douyin, xiaohongshu, bilibili
    status = Column(String(20), default="in_use", index=True)  # in_use, released, failed
    verification_code = Column(String(10))  # 验证码
    used_at = Column(DateTime, default=datetime.utcnow, index=True)  # 使用时间
    released_at = Column(DateTime, index=True)  # 释放时间


class NurturingSession(Base):
    """养号会话记录表"""
    __tablename__ = "nurturing_sessions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), index=True)
    
    # 会话信息
    session_date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer)  # 会话持续时间（分钟）
    actions_performed = Column(JSON)  # 执行的操作列表
    
    # 行为统计
    browse_count = Column(Integer, default=0)  # 浏览数量
    like_count = Column(Integer, default=0)  # 点赞数量
    comment_count = Column(Integer, default=0)  # 评论数量
    share_count = Column(Integer, default=0)  # 分享数量
    
    # 关联关系
    account = relationship("Account", back_populates="nurturing_sessions")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AccountHealthMetrics(Base):
    """账号健康度指标表"""
    __tablename__ = "account_health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), unique=True, index=True)
    
    # 健康度评分
    overall_score = Column(Float, default=100.0)  # 总体健康度
    activity_score = Column(Float, default=100.0)  # 活跃度
    engagement_score = Column(Float, default=100.0)  # 互动度
    compliance_score = Column(Float, default=100.0)  # 合规度
    
    # 风险指标
    risk_level = Column(String(20), default="low")  # low, medium, high
    warning_count = Column(Integer, default=0)  # 警告次数
    
    # 最近活动
    last_active = Column(DateTime)
    last_check = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    account = relationship("Account", back_populates="health_metrics")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LLMProviderEnum(str, enum.Enum):
    """大模型提供商枚举"""
    SILICONFLOW = "siliconflow"
    MODELSCOPE = "modelscope"
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


class FunctionTypeEnum(str, enum.Enum):
    """功能类型枚举"""
    COPYWRITING = "copywriting"  # 文案生成
    COVER_GENERATION = "cover_generation"  # 封面图生成
    IMAGE_GENERATION = "image_generation"  # 配图生成
    CONTENT_ANALYSIS = "content_analysis"  # 内容分析


class LLMConfig(Base):
    """大模型配置表"""
    __tablename__ = "llm_configs"
    
    # 索引优化
    __table_args__ = (
        Index('idx_provider_function', 'provider', 'function_type'),
        Index('idx_is_default', 'is_default'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # 基础信息
    provider = Column(Enum(LLMProviderEnum, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    function_type = Column(Enum(FunctionTypeEnum, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # 配置名称
    
    # API配置
    api_key = Column(String(500))  # API密钥（加密存储）
    base_url = Column(String(500))  # API基础URL
    model_name = Column(String(200), nullable=False)  # 模型名称
    
    # 图像模型专用字段
    image_model_name = Column(String(200))  # 图像生成模型名称
    
    # 配置参数
    timeout = Column(Integer, default=60)  # 超时时间（秒）
    max_tokens = Column(Integer, default=4096)  # 最大token数
    temperature = Column(Float, default=0.7)  # 温度参数
    extra_params = Column(JSON)  # 额外参数（JSON格式）
    
    # 状态标识
    is_default = Column(Boolean, default=False, index=True)  # 是否为默认配置
    is_active = Column(Boolean, default=True, index=True)  # 是否启用
    priority = Column(Integer, default=0)  # 优先级（数字越大优先级越高）
    
    # 描述信息
    description = Column(Text)  # 配置描述
    
    # 测试信息
    last_test_time = Column(DateTime)  # 最后测试时间
    last_test_status = Column(String(20))  # 最后测试结果：success/failed
    last_test_error = Column(Text)  # 最后测试错误信息
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemConfig(Base):
    """系统配置表 - 存储所有系统配置项"""
    __tablename__ = "system_configs"
    
    # 索引优化
    __table_args__ = (
        Index('idx_config_category', 'category'),
        Index('idx_config_key', 'config_key', unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # 配置分类
    category = Column(String(50), nullable=False, index=True)  # 配置分类：database, redis, celery, jwt, nurturing, playwright, alert, sms, hot_trend等
    config_key = Column(String(100), nullable=False, unique=True, index=True)  # 配置键
    config_value = Column(Text)  # 配置值（文本格式）
    value_type = Column(String(20), default="string")  # 值类型：string/int/float/bool/json/list
    
    # 配置信息
    description = Column(Text)  # 配置描述
    is_encrypted = Column(Boolean, default=False)  # 是否加密存储
    is_required = Column(Boolean, default=False)  # 是否必需
    default_value = Column(Text)  # 默认值
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
