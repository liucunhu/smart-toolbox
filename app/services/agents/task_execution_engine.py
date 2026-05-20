"""
智能体任务执行引擎 - Phase 4
负责调度和执行各种类型的智能体任务
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TaskExecutor(ABC):
    """任务执行器基类"""
    
    @abstractmethod
    async def execute(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task_params: 任务参数
            
        Returns:
            执行结果
        """
        pass
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        """返回智能体类型"""
        pass


class TaskExecutionEngine:
    """任务执行引擎 - 管理和调度所有任务执行器"""
    
    def __init__(self):
        self.executors: Dict[str, TaskExecutor] = {}
        self.task_history: list = []
        logger.info("任务执行引擎初始化完成")
    
    def register_executor(self, executor: TaskExecutor):
        """注册任务执行器"""
        agent_type = executor.agent_type
        self.executors[agent_type] = executor
        logger.info(f"注册任务执行器: {agent_type}")
    
    async def execute_task(
        self,
        agent_type: str,
        task_params: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            agent_type: 智能体类型
            task_params: 任务参数
            task_id: 任务ID（可选）
            
        Returns:
            执行结果
        """
        if agent_type not in self.executors:
            raise ValueError(f"未找到智能体类型 '{agent_type}' 的执行器")
        
        executor = self.executors[agent_type]
        
        start_time = datetime.now()
        logger.info(f"开始执行任务: {agent_type}, 任务ID: {task_id}")
        
        try:
            result = await executor.execute(task_params)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 记录任务历史
            history_record = {
                "task_id": task_id,
                "agent_type": agent_type,
                "status": "success",
                "duration": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "result": result
            }
            self.task_history.append(history_record)
            
            logger.info(f"任务执行成功: {agent_type}, 耗时: {duration:.2f}秒")
            
            return {
                "status": "success",
                "agent_type": agent_type,
                "task_id": task_id,
                "duration": duration,
                "data": result
            }
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            error_msg = f"任务执行失败: {agent_type}, 错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 记录失败历史
            history_record = {
                "task_id": task_id,
                "agent_type": agent_type,
                "status": "failed",
                "duration": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "error": str(e)
            }
            self.task_history.append(history_record)
            
            return {
                "status": "failed",
                "agent_type": agent_type,
                "task_id": task_id,
                "duration": duration,
                "error": str(e)
            }
    
    def get_task_history(self, limit: int = 50) -> list:
        """获取任务执行历史"""
        return self.task_history[-limit:]
    
    def get_executor_stats(self) -> Dict[str, Any]:
        """获取执行器统计信息"""
        stats = {}
        for agent_type in self.executors.keys():
            type_history = [h for h in self.task_history if h["agent_type"] == agent_type]
            success_count = len([h for h in type_history if h["status"] == "success"])
            failed_count = len([h for h in type_history if h["status"] == "failed"])
            
            stats[agent_type] = {
                "total_tasks": len(type_history),
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_count / len(type_history) if type_history else 0
            }
        
        return stats


# 全局执行引擎实例
execution_engine = TaskExecutionEngine()
