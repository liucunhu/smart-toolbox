"""
智能养号系统数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class NurturingSession(Base):
    """养号会话记录"""
    __tablename__ = "nurturing_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    
    # 会话信息
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="in_progress", index=True)  # in_progress/completed/failed
    
    # 浏览信息
    category = Column(String(100), nullable=True)
    is_active_time = Column(Boolean, default=True)
    
    # 统计信息
    videos_watched = Column(Integer, default=0)
    total_watch_duration = Column(Integer, default=0)  # 总观看时长（秒）
    
    # 互动统计
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    forward_count = Column(Integer, default=0)
    follow_count = Column(Integer, default=0)
    collect_count = Column(Integer, default=0)
    
    # 详细记录
    browse_records = Column(JSON, nullable=True)  # 详细浏览记录
    error_message = Column(Text, nullable=True)
    
    # 关联
    account = relationship("Account", back_populates="nurturing_sessions")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NurturingVideoRecord(Base):
    """单个视频浏览记录"""
    __tablename__ = "nurturing_video_records"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("nurturing_sessions.id"), nullable=False, index=True)
    
    # 视频信息
    platform = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    video_title = Column(String(500), nullable=True)
    video_author = Column(String(200), nullable=True)
    
    # 浏览信息
    watch_duration = Column(Integer, nullable=False)  # 观看时长（秒）
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 互动信息
    interactions = Column(JSON, nullable=True)  # ["like", "comment", ...]
    
    # 关联
    session = relationship("NurturingSession", back_populates="video_records")", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AccountHealthMetrics(Base):
    """账号健康度指标"""
    __tablename__ = "account_health_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, unique=True, index=True)
    
    # 基础健康度
    health_score = Column(Float, default=60.0)  # 0-100分
    last_nurturing_time = Column(DateTime, nullable=True)
    nurturing_days = Column(Integer, default=0)  # 养号天数
    
    # 活跃度指标
    total_videos_watched = Column(Integer, default=0)
    total_watch_duration = Column(Integer, default=0)  # 总观看时长（秒）
    total_likes = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    total_forwards = Column(Integer, default=0)
    total_follows = Column(Integer, default=0)
    
    # 风险指标
    risk_level = Column(String(20), default="low")  # low/medium/high
    risk_reason = Column(Text, nullable=True)
    last_risk_check = Column(DateTime, nullable=True)
    
    # 状态监控
    is_limited = Column(Boolean, default=False)  # 是否被限流
    is_banned = Column(Boolean, default=False)  # 是否被封号
    ban_reason = Column(Text, nullable=True)
    
    # 关联
    account = relationship("Account", back_populates="health_metrics")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 更新Account模型的关联关系
# 需要在app/models/__init__.py中添加这些关联
