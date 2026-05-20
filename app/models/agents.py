"""
智能体协作系统数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base


class AgentWorkflow(Base):
    """工作流定义表"""
    __tablename__ = "agent_workflows"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0.0")
    
    # 工作流JSON定义
    definition = Column(JSON, nullable=False)
    
    # 状态
    status = Column(String(20), default="active", index=True)  # active/inactive/archived
    
    # 元数据（使用workflow_metadata避免与SQLAlchemy保留字冲突）
    workflow_metadata = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    instances = relationship("AgentWorkflowInstance", back_populates="workflow", cascade="all, delete-orphan")


class AgentWorkflowInstance(Base):
    """工作流实例表"""
    __tablename__ = "agent_workflow_instances"
    
    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("agent_workflows.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # 执行状态
    status = Column(String(20), default="pending", index=True)  # pending/running/completed/failed
    current_node_id = Column(String(36), nullable=True)
    
    # 变量和结果
    variables = Column(JSON, nullable=True)
    node_results = Column(JSON, nullable=True)
    
    # 时间信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 错误信息
    error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    workflow = relationship("AgentWorkflow", back_populates="instances")


class AgentExperience(Base):
    """经验记录表"""
    __tablename__ = "agent_experiences"
    
    id = Column(String(36), primary_key=True)
    
    # 任务信息
    task_type = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    
    # 上下文和结果
    context = Column(JSON, nullable=True)
    result = Column(String(20), nullable=False, index=True)  # success/failed
    reward = Column(Float, default=0.0)
    
    # 元数据（使用experience_metadata避免与SQLAlchemy保留字冲突）
    experience_metadata = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AgentCoordinationLog(Base):
    """协作日志表"""
    __tablename__ = "agent_coordination_logs"
    
    id = Column(String(36), primary_key=True)
    
    # 任务和智能体信息
    task_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    
    # 动作信息
    action = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # started/completed/failed
    
    # 性能信息
    duration = Column(Float, nullable=True)  # 执行时长（秒）
    
    # 错误信息
    error = Column(Text, nullable=True)
    
    # 额外数据
    data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AgentInfo(Base):
    """智能体信息表"""
    __tablename__ = "agent_infos"
    
    id = Column(String(36), primary_key=True)
    agent_type = Column(String(100), nullable=False, index=True)  # content_generation/compliance_check/etc
    
    # 状态信息
    status = Column(String(20), default="idle", index=True)  # idle/busy/error/offline
    current_task_id = Column(String(36), nullable=True)
    
    # 能力列表
    capabilities = Column(JSON, nullable=True)
    
    # 统计信息
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    load = Column(Float, default=0.0)  # 负载 0-1
    
    # 心跳
    last_heartbeat = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
