"""
工作流自动编排引擎 - Phase 5
负责自动执行分解的任务序列，管理依赖关系和结果传递
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class WorkflowTask:
    """工作流中的任务"""
    
    def __init__(self, task_id: str, agent_type: str, params: Dict[str, Any], 
                 dependencies: List[str] = None, retry_count: int = 3):
        self.task_id = task_id
        self.agent_type = agent_type
        self.params = params
        self.dependencies = dependencies or []
        self.retry_count = retry_count
        self.max_retries = retry_count
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.duration = 0
    
    def can_execute(self, completed_tasks: set) -> bool:
        """检查是否可以执行（所有依赖已完成）"""
        return all(dep in completed_tasks for dep in self.dependencies)


class WorkflowInstance:
    """工作流实例"""
    
    def __init__(self, workflow_id: str, name: str, description: str = ""):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.tasks: List[WorkflowTask] = []
        self.status = WorkflowStatus.PENDING
        self.context: Dict[str, Any] = {}  # 共享上下文
        self.start_time = None
        self.end_time = None
        self.completed_tasks: set = set()
        self.failed_tasks: set = set()
    
    def add_task(self, task: WorkflowTask):
        """添加任务到工作流"""
        self.tasks.append(task)
    
    def get_pending_tasks(self) -> List[WorkflowTask]:
        """获取待执行的任务"""
        return [
            task for task in self.tasks
            if task.status == TaskStatus.PENDING and task.can_execute(self.completed_tasks)
        ]
    
    def get_progress(self) -> float:
        """获取执行进度（0-1）"""
        if not self.tasks:
            return 0.0
        return len(self.completed_tasks) / len(self.tasks)


class WorkflowOrchestrator:
    """工作流编排器 - 自动执行任务序列"""
    
    def __init__(self, execution_engine):
        self.execution_engine = execution_engine
        self.workflows: Dict[str, WorkflowInstance] = {}
        self.active_workflows: set = set()
        logger.info("工作流编排器初始化完成")
    
    def create_workflow(self, name: str, description: str = "") -> WorkflowInstance:
        """创建工作流实例"""
        workflow_id = str(uuid.uuid4())
        workflow = WorkflowInstance(workflow_id, name, description)
        self.workflows[workflow_id] = workflow
        logger.info(f"创建工作流: {name} ({workflow_id})")
        return workflow
    
    def build_workflow_from_tasks(self, decomposed_tasks: List[Dict[str, Any]], 
                                   workflow_name: str = "Auto Workflow") -> WorkflowInstance:
        """从分解的任务构建工作流"""
        workflow = self.create_workflow(workflow_name)
        
        # 创建任务映射
        task_map = {}
        for i, task_info in enumerate(decomposed_tasks):
            task_id = task_info.get('task_id', f"task_{i}")
            agent_type = task_info.get('agent_type', 'general')
            
            # 构建任务参数
            params = {
                "task_type": task_info.get('description', '').split(' - ')[1] if ' - ' in task_info.get('description', '') else 'default',
                "description": task_info.get('description', ''),
                "priority": task_info.get('priority', 5)
            }
            
            # 设置依赖关系（顺序执行）
            dependencies = []
            if i > 0:
                prev_task_id = decomposed_tasks[i-1].get('task_id', f"task_{i-1}")
                dependencies.append(prev_task_id)
            
            task = WorkflowTask(
                task_id=task_id,
                agent_type=agent_type,
                params=params,
                dependencies=dependencies,
                retry_count=3
            )
            
            workflow.add_task(task)
            task_map[task_id] = task
        
        logger.info(f"构建工作流完成，共 {len(workflow.tasks)} 个任务")
        return workflow
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """执行工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status == WorkflowStatus.RUNNING:
            raise ValueError("工作流正在运行中")
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now()
        self.active_workflows.add(workflow_id)
        
        logger.info(f"开始执行工作流: {workflow.name} ({workflow_id})")
        
        try:
            await self._execute_workflow_tasks(workflow)
            
            # 判断工作流状态
            if workflow.failed_tasks:
                workflow.status = WorkflowStatus.FAILED
                logger.warning(f"工作流执行失败: {workflow_id}, 失败任务数: {len(workflow.failed_tasks)}")
            else:
                workflow.status = WorkflowStatus.COMPLETED
                logger.info(f"工作流执行成功: {workflow_id}")
            
            workflow.end_time = datetime.now()
            self.active_workflows.discard(workflow_id)
            
            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "progress": workflow.get_progress(),
                "total_tasks": len(workflow.tasks),
                "completed_tasks": len(workflow.completed_tasks),
                "failed_tasks": len(workflow.failed_tasks),
                "duration": (workflow.end_time - workflow.start_time).total_seconds(),
                "context": workflow.context
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.end_time = datetime.now()
            self.active_workflows.discard(workflow_id)
            logger.error(f"工作流执行异常: {workflow_id}, 错误: {str(e)}")
            raise
    
    async def _execute_workflow_tasks(self, workflow: WorkflowInstance):
        """执行工作流中的所有任务"""
        max_iterations = len(workflow.tasks) * 2  # 防止无限循环
        iteration = 0
        
        while workflow.completed_tasks | workflow.failed_tasks != set(range(len(workflow.tasks))) and iteration < max_iterations:
            iteration += 1
            
            # 获取可执行的任务
            pending_tasks = workflow.get_pending_tasks()
            
            if not pending_tasks:
                # 没有可执行的任务，检查是否有未完成的任务
                uncompleted = [t for t in workflow.tasks if t.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]]
                if uncompleted:
                    logger.warning(f"工作流停滞，有 {len(uncompleted)} 个任务无法执行")
                    break
                else:
                    break
            
            # 并行执行可执行的任务
            tasks_to_execute = []
            for task in pending_tasks:
                task.status = TaskStatus.RUNNING
                task.start_time = datetime.now()
                tasks_to_execute.append(self._execute_single_task(workflow, task))
            
            # 等待所有任务完成
            if tasks_to_execute:
                await asyncio.gather(*tasks_to_execute, return_exceptions=True)
            
            # 短暂延迟，避免过度占用资源
            await asyncio.sleep(0.1)
    
    async def _execute_single_task(self, workflow: WorkflowInstance, task: WorkflowTask):
        """执行单个任务（带重试机制）"""
        last_error = None
        
        for attempt in range(task.max_retries):
            try:
                logger.info(f"执行任务: {task.task_id}, 尝试 {attempt + 1}/{task.max_retries}")
                
                # 注入上下文到任务参数
                task_params = {**task.params, "context": workflow.context}
                
                # 执行任务
                result = await self.execution_engine.execute_task(
                    agent_type=task.agent_type,
                    task_params=task_params,
                    task_id=task.task_id
                )
                
                if result["status"] == "success":
                    # 任务成功
                    task.status = TaskStatus.COMPLETED
                    task.result = result["data"]
                    task.end_time = datetime.now()
                    task.duration = (task.end_time - task.start_time).total_seconds()
                    
                    # 将结果存入上下文
                    workflow.context[task.task_id] = result["data"]
                    workflow.completed_tasks.add(task.task_id)
                    
                    logger.info(f"任务执行成功: {task.task_id}, 耗时: {task.duration:.2f}秒")
                    return
                
                else:
                    # 任务失败
                    last_error = result.get("error", "未知错误")
                    logger.warning(f"任务执行失败: {task.task_id}, 错误: {last_error}")
                    
                    if attempt < task.max_retries - 1:
                        task.status = TaskStatus.RETRYING
                        await asyncio.sleep(1)  # 重试前等待1秒
                    else:
                        raise Exception(last_error)
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"任务执行异常: {task.task_id}, 错误: {str(e)}")
                
                if attempt < task.max_retries - 1:
                    task.status = TaskStatus.RETRYING
                    await asyncio.sleep(1)  # 重试前等待1秒
        
        # 所有重试都失败
        task.status = TaskStatus.FAILED
        task.error = last_error
        task.end_time = datetime.now()
        task.duration = (task.end_time - task.start_time).total_seconds() if task.start_time else 0
        workflow.failed_tasks.add(task.task_id)
        
        logger.error(f"任务最终失败: {task.task_id}, 错误: {last_error}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流状态"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress": workflow.get_progress(),
            "total_tasks": len(workflow.tasks),
            "completed_tasks": len(workflow.completed_tasks),
            "failed_tasks": len(workflow.failed_tasks),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "agent_type": task.agent_type,
                    "status": task.status.value,
                    "duration": task.duration,
                    "error": task.error
                }
                for task in workflow.tasks
            ],
            "context_keys": list(workflow.context.keys()),
            "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
            "end_time": workflow.end_time.isoformat() if workflow.end_time else None
        }
    
    def list_workflows(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出工作流"""
        workflows = []
        for wf_id, wf in self.workflows.items():
            if status and wf.status.value != status:
                continue
            
            workflows.append({
                "workflow_id": wf_id,
                "name": wf.name,
                "status": wf.status.value,
                "progress": wf.get_progress(),
                "total_tasks": len(wf.tasks),
                "created_at": wf.start_time.isoformat() if wf.start_time else None
            })
        
        return workflows


# 全局工作流编排器实例（需要在应用启动时初始化）
workflow_orchestrator: Optional[WorkflowOrchestrator] = None


def get_workflow_orchestrator(execution_engine=None):
    """获取工作流编排器实例"""
    global workflow_orchestrator
    if workflow_orchestrator is None:
        if execution_engine is None:
            raise ValueError("首次初始化需要提供 execution_engine")
        workflow_orchestrator = WorkflowOrchestrator(execution_engine)
    return workflow_orchestrator
