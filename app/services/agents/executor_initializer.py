"""
执行器初始化模块
在应用启动时注册所有任务执行器
"""
import logging
from app.services.agents.task_execution_engine import execution_engine
from app.services.agents.executors import (
    research_executor,
    content_executor,
    compliance_executor,
    image_executor,
    distribution_executor,
    planning_executor,
    nurturing_executor,
    general_executor
)

logger = logging.getLogger(__name__)


def initialize_executors():
    """初始化并注册所有任务执行器"""
    logger.info("开始初始化任务执行器...")
    
    # 注册所有执行器
    executors = [
        research_executor,      # 研究智能体
        content_executor,       # 内容生成智能体
        compliance_executor,    # 合规检查智能体
        image_executor,         # 图片生成智能体
        distribution_executor,  # 分发智能体
        planning_executor,      # 规划智能体
        nurturing_executor,     # 养号智能体
        general_executor        # 通用智能体
    ]
    
    for executor in executors:
        execution_engine.register_executor(executor)
    
    logger.info(f"成功注册 {len(executors)} 个任务执行器")
    logger.info(f"已注册的智能体类型: {list(execution_engine.executors.keys())}")


# 导出全局执行引擎
__all__ = ["initialize_executors", "execution_engine"]
