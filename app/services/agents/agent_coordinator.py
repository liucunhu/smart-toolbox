"""
智能体协调器 - 多智能体协作系统核心
负责任务分解、智能体调度、冲突解决和负载均衡
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """智能体状态"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentInfo:
    """智能体信息"""
    agent_id: str
    agent_type: str  # 选题、创作、分发、养号、分析、优化
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    load: float = 0.0  # 负载 0-1
    last_heartbeat: Optional[datetime] = None
    
    def is_available(self) -> bool:
        return self.status == AgentStatus.IDLE and self.load < 0.8


@dataclass
class SubTask:
    """子任务"""
    task_id: str
    parent_task_id: str
    description: str
    agent_type: str  # 需要的智能体类型
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinationTask:
    """协调任务"""
    task_id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    subtasks: List[SubTask] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConflictResolver:
    """冲突解决器"""
    
    def __init__(self):
        self.resource_locks: Dict[str, asyncio.Lock] = {}
    
    async def resolve_resource_conflict(
        self,
        resource_id: str,
        agent_id: str,
        timeout: float = 30.0
    ) -> bool:
        """解决资源冲突
        
        Args:
            resource_id: 资源ID（如账号ID、平台名称）
            agent_id: 请求资源的智能体ID
            timeout: 超时时间（秒）
            
        Returns:
            是否成功获取资源
        """
        if resource_id not in self.resource_locks:
            self.resource_locks[resource_id] = asyncio.Lock()
        
        lock = self.resource_locks[resource_id]
        
        try:
            await asyncio.wait_for(lock.acquire(), timeout=timeout)
            logger.info(f"智能体 {agent_id} 成功获取资源 {resource_id}")
            return True
        except asyncio.TimeoutError:
            logger.warning(f"智能体 {agent_id} 获取资源 {resource_id} 超时")
            return False
    
    def release_resource(self, resource_id: str, agent_id: str):
        """释放资源"""
        if resource_id in self.resource_locks:
            try:
                self.resource_locks[resource_id].release()
                logger.info(f"智能体 {agent_id} 释放资源 {resource_id}")
            except RuntimeError:
                logger.warning(f"资源 {resource_id} 未被锁定")


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
    
    def register_agent(self, agent: AgentInfo):
        """注册智能体"""
        self.agents[agent.agent_id] = agent
        logger.info(f"注册智能体: {agent.agent_id} ({agent.agent_type})")
    
    def unregister_agent(self, agent_id: str):
        """注销智能体"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"注销智能体: {agent_id}")
    
    def select_best_agent(self, required_type: str) -> Optional[str]:
        """选择最佳智能体
        
        Args:
            required_type: 需要的智能体类型
            
        Returns:
            最佳智能体ID，如果没有可用则返回None
        """
        available_agents = [
            agent for agent in self.agents.values()
            if agent.agent_type == required_type and agent.is_available()
        ]
        
        if not available_agents:
            return None
        
        # 按负载从小到大排序，选择负载最低的
        best_agent = min(available_agents, key=lambda a: a.load)
        return best_agent.agent_id
    
    def update_agent_load(self, agent_id: str, load: float):
        """更新智能体负载"""
        if agent_id in self.agents:
            self.agents[agent_id].load = max(0.0, min(1.0, load))
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        stats = {
            "total": len(self.agents),
            "idle": sum(1 for a in self.agents.values() if a.status == AgentStatus.IDLE),
            "busy": sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY),
            "error": sum(1 for a in self.agents.values() if a.status == AgentStatus.ERROR),
            "by_type": {}
        }
        
        for agent in self.agents.values():
            if agent.agent_type not in stats["by_type"]:
                stats["by_type"][agent.agent_type] = {"total": 0, "idle": 0, "busy": 0}
            stats["by_type"][agent.agent_type]["total"] += 1
            if agent.status == AgentStatus.IDLE:
                stats["by_type"][agent.agent_type]["idle"] += 1
            elif agent.status == AgentStatus.BUSY:
                stats["by_type"][agent.agent_type]["busy"] += 1
        
        return stats


class ExperiencePool:
    """经验池 - 存储成功/失败案例供学习"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.experiences: List[Dict[str, Any]] = []
        self.patterns: Dict[str, int] = {}  # 模式识别
    
    def add_experience(
        self,
        task_type: str,
        action: str,
        context: Dict[str, Any],
        result: str,  # success/failed
        reward: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加经验
        
        Args:
            task_type: 任务类型
            action: 执行的动作
            context: 上下文信息
            result: 结果（success/failed）
            reward: 奖励值（-1到1）
            metadata: 额外元数据
        """
        experience = {
            "id": str(uuid.uuid4()),
            "task_type": task_type,
            "action": action,
            "context": context,
            "result": result,
            "reward": reward,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.experiences.append(experience)
        
        # 保持经验池大小
        if len(self.experiences) > self.max_size:
            self.experiences = self.experiences[-self.max_size:]
        
        # 更新模式计数
        pattern_key = f"{task_type}:{action}:{result}"
        self.patterns[pattern_key] = self.patterns.get(pattern_key, 0) + 1
        
        logger.debug(f"添加经验: {task_type} - {action} - {result} (reward={reward})")
    
    def query_similar_experiences(
        self,
        task_type: str,
        context: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """查询相似经验
        
        Args:
            task_type: 任务类型
            context: 当前上下文
            limit: 返回数量限制
            
        Returns:
            相似经验列表
        """
        # 简单实现：按任务类型过滤，按奖励排序
        similar = [
            exp for exp in self.experiences
            if exp["task_type"] == task_type
        ]
        
        # 按奖励降序排序
        similar.sort(key=lambda x: x["reward"], reverse=True)
        
        return similar[:limit]
    
    def get_best_practice(self, task_type: str, action: str) -> Optional[Dict[str, Any]]:
        """获取最佳实践
        
        Args:
            task_type: 任务类型
            action: 动作
            
        Returns:
            最佳实践经验，如果没有则返回None
        """
        experiences = [
            exp for exp in self.experiences
            if exp["task_type"] == task_type and exp["action"] == action
        ]
        
        if not experiences:
            return None
        
        # 返回奖励最高的经验
        return max(experiences, key=lambda x: x["reward"])
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取经验统计"""
        total = len(self.experiences)
        success_count = sum(1 for exp in self.experiences if exp["result"] == "success")
        failed_count = sum(1 for exp in self.experiences if exp["result"] == "failed")
        
        avg_reward = (
            sum(exp["reward"] for exp in self.experiences) / total
            if total > 0 else 0
        )
        
        return {
            "total_experiences": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": success_count / total if total > 0 else 0,
            "average_reward": avg_reward,
            "pattern_count": len(self.patterns)
        }


class AgentCoordinator:
    """智能体协调器 - 核心类
    
    负责任务分解、智能体调度、冲突解决和负载均衡
    """
    
    def __init__(self):
        self.tasks: Dict[str, CoordinationTask] = {}
        self.agents: Dict[str, AgentInfo] = {}
        self.load_balancer = LoadBalancer()
        self.conflict_resolver = ConflictResolver()
        self.experience_pool = ExperiencePool()
        self.task_handlers: Dict[str, Callable] = {}
        
        logger.info("智能体协调器初始化完成")
    
    def register_agent(self, agent: AgentInfo):
        """注册智能体"""
        self.agents[agent.agent_id] = agent
        self.load_balancer.register_agent(agent)
        logger.info(f"智能体已注册: {agent.agent_id} ({agent.agent_type})")
    
    def unregister_agent(self, agent_id: str):
        """注销智能体"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.load_balancer.unregister_agent(agent_id)
            logger.info(f"智能体已注销: {agent_id}")
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 处理函数（异步）
        """
        self.task_handlers[task_type] = handler
        logger.info(f"任务处理器已注册: {task_type}")
    
    async def decompose_task(
        self,
        task_name: str,
        description: str,
        subtask_definitions: List[Dict[str, Any]],
        priority: TaskPriority = TaskPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CoordinationTask:
        """分解任务为子任务
        
        Args:
            task_name: 任务名称
            description: 任务描述
            subtask_definitions: 子任务定义列表
            priority: 任务优先级
            metadata: 元数据
            
        Returns:
            协调任务对象
        """
        task_id = str(uuid.uuid4())
        
        coordination_task = CoordinationTask(
            task_id=task_id,
            name=task_name,
            description=description,
            priority=priority,
            metadata=metadata or {}
        )
        
        # 创建子任务
        for i, subtask_def in enumerate(subtask_definitions):
            subtask = SubTask(
                task_id=str(uuid.uuid4()),
                parent_task_id=task_id,
                description=subtask_def.get("description", f"子任务 {i+1}"),
                agent_type=subtask_def.get("agent_type", "general"),
                priority=subtask_def.get("priority", TaskPriority.MEDIUM),
                metadata=subtask_def.get("metadata", {})
            )
            coordination_task.subtasks.append(subtask)
        
        self.tasks[task_id] = coordination_task
        logger.info(f"任务已分解: {task_name} ({len(coordination_task.subtasks)}个子任务)")
        
        return coordination_task
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """执行协调任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行结果
        """
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        logger.info(f"开始执行任务: {task.name} ({task_id})")
        
        results = []
        errors = []
        
        # 并行执行所有子任务
        subtask_tasks = []
        for subtask in task.subtasks:
            subtask_tasks.append(self._execute_subtask(subtask))
        
        # 等待所有子任务完成
        subtask_results = await asyncio.gather(*subtask_tasks, return_exceptions=True)
        
        for i, result in enumerate(subtask_results):
            subtask = task.subtasks[i]
            
            if isinstance(result, Exception):
                subtask.status = TaskStatus.FAILED
                subtask.error = str(result)
                errors.append({
                    "subtask_id": subtask.task_id,
                    "error": str(result)
                })
                logger.error(f"子任务失败: {subtask.task_id} - {result}")
            else:
                subtask.status = TaskStatus.COMPLETED
                subtask.result = result
                subtask.completed_at = datetime.now()
                results.append({
                    "subtask_id": subtask.task_id,
                    "result": result
                })
                
                # 记录成功经验
                self.experience_pool.add_experience(
                    task_type=subtask.agent_type,
                    action="execute",
                    context=subtask.metadata,
                    result="success",
                    reward=0.8
                )
        
        # 判断整体任务状态
        if errors:
            task.status = TaskStatus.FAILED
            task.error = f"{len(errors)}个子任务失败"
            logger.warning(f"任务部分失败: {task.name} - {len(errors)}个错误")
        else:
            task.status = TaskStatus.COMPLETED
            task.result = results
            logger.info(f"任务执行成功: {task.name}")
        
        task.completed_at = datetime.now()
        
        return {
            "task_id": task_id,
            "status": task.status.value,
            "results": results,
            "errors": errors,
            "total_subtasks": len(task.subtasks),
            "success_count": len(results),
            "failed_count": len(errors)
        }
    
    async def _execute_subtask(self, subtask: SubTask) -> Any:
        """执行单个子任务
        
        Args:
            subtask: 子任务对象
            
        Returns:
            执行结果
        """
        subtask.status = TaskStatus.RUNNING
        subtask.started_at = datetime.now()
        
        # 选择最佳智能体
        agent_id = self.load_balancer.select_best_agent(subtask.agent_type)
        
        if not agent_id:
            raise RuntimeError(f"没有可用的{subtask.agent_type}智能体")
        
        # 分配任务给智能体
        agent = self.agents[agent_id]
        agent.status = AgentStatus.BUSY
        agent.current_task = subtask.task_id
        subtask.assigned_agent = agent_id
        
        logger.info(f"子任务 {subtask.task_id} 分配给智能体 {agent_id}")
        
        try:
            # 获取任务处理器
            handler = self.task_handlers.get(subtask.agent_type)
            
            if not handler:
                raise RuntimeError(f"未注册{subtask.agent_type}类型的任务处理器")
            
            # 执行任务
            result = await handler(subtask)
            
            # 更新智能体状态
            agent.status = AgentStatus.IDLE
            agent.current_task = None
            agent.completed_tasks += 1
            self.load_balancer.update_agent_load(agent_id, 0.0)
            
            return result
            
        except Exception as e:
            # 更新智能体状态
            agent.status = AgentStatus.IDLE
            agent.current_task = None
            agent.failed_tasks += 1
            self.load_balancer.update_agent_load(agent_id, 0.0)
            
            # 记录失败经验
            self.experience_pool.add_experience(
                task_type=subtask.agent_type,
                action="execute",
                context=subtask.metadata,
                result="failed",
                reward=-0.5,
                metadata={"error": str(e)}
            )
            
            raise e
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status.value,
            "progress": self._calculate_progress(task),
            "subtasks": [
                {
                    "task_id": st.task_id,
                    "description": st.description,
                    "status": st.status.value,
                    "agent": st.assigned_agent
                }
                for st in task.subtasks
            ]
        }
    
    def _calculate_progress(self, task: CoordinationTask) -> float:
        """计算任务进度"""
        if not task.subtasks:
            return 0.0
        
        completed = sum(1 for st in task.subtasks if st.status == TaskStatus.COMPLETED)
        return completed / len(task.subtasks) * 100
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "total_tasks": len(self.tasks),
            "active_tasks": sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING),
            "agent_stats": self.load_balancer.get_agent_stats(),
            "experience_stats": self.experience_pool.get_statistics()
        }
