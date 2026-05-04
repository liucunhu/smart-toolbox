from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, Enum
from sqlalchemy.orm import declarative_base
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

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, index=True)
    content_task_id = Column(Integer, index=True)
    
    publish_status = Column(String(20), default="scheduled") # scheduled, published, failed
    publish_time = Column(DateTime)
    platform_url = Column(String(500)) # 发布后的链接
    
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertRecord(Base):
    """报警记录表"""
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # account_anomaly, task_failed, system_health
    subject = Column(String(200), nullable=False)  # 报警主题
    message = Column(Text)  # 报警详细内容
    status = Column(String(20), default="success")  # success, failed
    channels = Column(String(200))  # 发送渠道，逗号分隔（email,dingtalk）
    created_at = Column(DateTime, default=datetime.utcnow)


class PhoneRecord(Base):
    """手机号使用记录表"""
    __tablename__ = "phone_records"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # douyin, xiaohongshu, bilibili
    status = Column(String(20), default="in_use")  # in_use, released, failed
    verification_code = Column(String(10))  # 验证码
    used_at = Column(DateTime, default=datetime.utcnow)  # 使用时间
    released_at = Column(DateTime)  # 释放时间
