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
    username = Column(String(100), unique=True, index=True)
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
    
    # 关联关系
    nurturing_sessions = relationship("NurturingSession", back_populates="account", cascade="all, delete-orphan")
    health_metrics = relationship("AccountHealthMetrics", back_populates="account", uselist=False, cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContentTask(Base):
    """内容创作任务表"""
    __tablename__ = "content_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), unique=True, index=True)  # UUID
    original_topic = Column(Text)
    target_platform = Column(Enum(PlatformEnum, values_callable=lambda x: [e.value for e in x]))
    
    # 生成结果存储路径（视频类内容）
    script_path = Column(String(255))
    video_path = Column(String(255))
    cover_path = Column(String(255))
    
    # 头条文章特有字段
    article_title = Column(String(500))  # 文章标题
    article_content = Column(Text)  # 文章正文
    article_category = Column(String(100))  # 文章分类
    tags = Column(JSON)  # 标签列表
    
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

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
