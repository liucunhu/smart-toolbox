"""
工作流编排引擎 - 定义和执行复杂的工作流
支持条件分支、循环、并行执行等高级特性
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """节点类型"""
    START = "start"
    END = "end"
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """工作流节点"""
    node_id: str
    name: str
    node_type: NodeType
    description: str = ""
    
    # 任务相关
    task_type: Optional[str] = None  # 如果是TASK节点，指定任务类型
    task_params: Dict[str, Any] = field(default_factory=dict)
    
    # 条件相关
    condition: Optional[Callable] = None  # 如果是CONDITION节点，条件函数
    
    # 循环相关
    loop_count: int = 1  # 如果是LOOP节点，循环次数
    loop_variable: Optional[str] = None
    
    # 并行相关
    parallel_nodes: List[str] = field(default_factory=list)  # 并行执行的节点ID列表
    
    # 流程控制
    next_nodes: List[str] = field(default_factory=list)  # 后续节点ID列表
    on_success: Optional[str] = None  # 成功时的下一个节点
    on_failure: Optional[str] = None  # 失败时的下一个节点
    
    # 状态
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    nodes: Dict[str, WorkflowNode] = field(default_factory=dict)
    start_node_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowInstance:
    """工作流实例"""
    instance_id: str
    workflow_id: str
    name: str
    status: NodeStatus = NodeStatus.PENDING
    current_node_id: Optional[str] = None
    node_results: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)  # 工作流变量
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class TaskOrchestrator:
    """任务编排引擎
    
    负责定义、管理和执行复杂的工作流
    """
    
    def __init__(self, task_handler: Optional[Callable] = None):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        self.task_handler = task_handler
        
        logger.info("任务编排引擎初始化完成")
    
    def create_workflow(
        self,
        name: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowDefinition:
        """创建工作流定义
        
        Args:
            name: 工作流名称
            description: 工作流描述
            metadata: 元数据
            
        Returns:
            工作流定义对象
        """
        workflow_id = str(uuid.uuid4())
        
        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            metadata=metadata or {}
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"创建工作流: {name} ({workflow_id})")
        
        return workflow
    
    def add_node(
        self,
        workflow_id: str,
        name: str,
        node_type: NodeType,
        description: str = "",
        task_type: Optional[str] = None,
        task_params: Optional[Dict[str, Any]] = None,
        condition: Optional[Callable] = None,
        loop_count: int = 1,
        parallel_nodes: Optional[List[str]] = None,
        next_nodes: Optional[List[str]] = None,
        on_success: Optional[str] = None,
        on_failure: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加工作流节点
        
        Args:
            workflow_id: 工作流ID
            name: 节点名称
            node_type: 节点类型
            description: 节点描述
            task_type: 任务类型（TASK节点）
            task_params: 任务参数
            condition: 条件函数（CONDITION节点）
            loop_count: 循环次数（LOOP节点）
            parallel_nodes: 并行节点列表（PARALLEL节点）
            next_nodes: 后续节点列表
            on_success: 成功时的下一个节点
            on_failure: 失败时的下一个节点
            metadata: 元数据
            
        Returns:
            节点ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        node_id = str(uuid.uuid4())
        
        node = WorkflowNode(
            node_id=node_id,
            name=name,
            node_type=node_type,
            description=description,
            task_type=task_type,
            task_params=task_params or {},
            condition=condition,
            loop_count=loop_count,
            parallel_nodes=parallel_nodes or [],
            next_nodes=next_nodes or [],
            on_success=on_success,
            on_failure=on_failure,
            metadata=metadata or {}
        )
        
        self.workflows[workflow_id].nodes[node_id] = node
        
        # 如果是第一个节点，设置为起始节点
        if not self.workflows[workflow_id].start_node_id:
            self.workflows[workflow_id].start_node_id = node_id
        
        logger.debug(f"添加节点: {name} ({node_type.value}) 到工作流 {workflow_id}")
        
        return node_id
    
    def connect_nodes(
        self,
        workflow_id: str,
        from_node_id: str,
        to_node_id: str,
        condition: str = "on_success"
    ):
        """连接两个节点
        
        Args:
            workflow_id: 工作流ID
            from_node_id: 源节点ID
            to_node_id: 目标节点ID
            condition: 连接条件（on_success/on_failure）
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        if from_node_id not in workflow.nodes:
            raise ValueError(f"源节点不存在: {from_node_id}")
        
        if to_node_id not in workflow.nodes:
            raise ValueError(f"目标节点不存在: {to_node_id}")
        
        node = workflow.nodes[from_node_id]
        
        if condition == "on_success":
            node.on_success = to_node_id
        elif condition == "on_failure":
            node.on_failure = to_node_id
        
        if to_node_id not in node.next_nodes:
            node.next_nodes.append(to_node_id)
        
        logger.debug(f"连接节点: {from_node_id} -> {to_node_id} ({condition})")
    
    async def execute_workflow(
        self,
        workflow_id: str,
        initial_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流
        
        Args:
            workflow_id: 工作流ID
            initial_variables: 初始变量
            
        Returns:
            执行结果
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        if not workflow.start_node_id:
            raise ValueError(f"工作流没有起始节点: {workflow_id}")
        
        # 创建工作流实例
        instance_id = str(uuid.uuid4())
        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow_id=workflow_id,
            name=workflow.name,
            variables=initial_variables or {}
        )
        
        self.instances[instance_id] = instance
        
        logger.info(f"开始执行工作流实例: {workflow.name} ({instance_id})")
        
        try:
            # 从起始节点开始执行
            await self._execute_node(instance, workflow, workflow.start_node_id)
            
            instance.status = NodeStatus.COMPLETED
            instance.completed_at = datetime.now()
            
            logger.info(f"工作流实例执行成功: {instance_id}")
            
            return {
                "instance_id": instance_id,
                "status": "completed",
                "results": instance.node_results,
                "variables": instance.variables
            }
            
        except Exception as e:
            instance.status = NodeStatus.FAILED
            instance.error = str(e)
            instance.completed_at = datetime.now()
            
            logger.error(f"工作流实例执行失败: {instance_id} - {e}")
            
            return {
                "instance_id": instance_id,
                "status": "failed",
                "error": str(e),
                "results": instance.node_results
            }
    
    async def _execute_node(
        self,
        instance: WorkflowInstance,
        workflow: WorkflowDefinition,
        node_id: str
    ):
        """执行单个节点
        
        Args:
            instance: 工作流实例
            workflow: 工作流定义
            node_id: 节点ID
        """
        if node_id not in workflow.nodes:
            raise ValueError(f"节点不存在: {node_id}")
        
        node = workflow.nodes[node_id]
        instance.current_node_id = node_id
        node.status = NodeStatus.RUNNING
        
        logger.debug(f"执行节点: {node.name} ({node.node_type.value})")
        
        try:
            # 根据节点类型执行不同逻辑
            if node.node_type == NodeType.START:
                await self._execute_start_node(instance, node)
            elif node.node_type == NodeType.END:
                await self._execute_end_node(instance, node)
            elif node.node_type == NodeType.TASK:
                await self._execute_task_node(instance, node)
            elif node.node_type == NodeType.CONDITION:
                await self._execute_condition_node(instance, node)
            elif node.node_type == NodeType.PARALLEL:
                await self._execute_parallel_node(instance, workflow, node)
            elif node.node_type == NodeType.LOOP:
                await self._execute_loop_node(instance, workflow, node)
            
            node.status = NodeStatus.COMPLETED
            instance.node_results[node_id] = node.result
            
            # 确定下一个节点
            next_node_id = self._get_next_node(node, success=True)
            
            if next_node_id:
                await self._execute_node(instance, workflow, next_node_id)
            
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            instance.node_results[node_id] = {"error": str(e)}
            
            # 确定失败时的下一个节点
            next_node_id = self._get_next_node(node, success=False)
            
            if next_node_id:
                await self._execute_node(instance, workflow, next_node_id)
            else:
                raise e
    
    async def _execute_start_node(self, instance: WorkflowInstance, node: WorkflowNode):
        """执行起始节点"""
        node.result = {"started_at": datetime.now().isoformat()}
        logger.debug(f"工作流启动: {instance.instance_id}")
    
    async def _execute_end_node(self, instance: WorkflowInstance, node: WorkflowNode):
        """执行结束节点"""
        node.result = {"completed_at": datetime.now().isoformat()}
        logger.debug(f"工作流结束: {instance.instance_id}")
    
    async def _execute_task_node(self, instance: WorkflowInstance, node: WorkflowNode):
        """执行任务节点"""
        if not self.task_handler:
            raise RuntimeError("未设置任务处理器")
        
        # 准备任务参数
        task_params = node.task_params.copy()
        
        # 替换变量
        for key, value in task_params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                if var_name in instance.variables:
                    task_params[key] = instance.variables[var_name]
        
        # 执行任务
        result = await self.task_handler(
            task_type=node.task_type,
            params=task_params,
            context={
                "instance_id": instance.instance_id,
                "node_id": node.node_id,
                "variables": instance.variables
            }
        )
        
        node.result = result
        
        # 如果任务返回了变量更新，合并到工作流变量中
        if isinstance(result, dict) and "variables" in result:
            instance.variables.update(result["variables"])
    
    async def _execute_condition_node(self, instance: WorkflowInstance, node: WorkflowNode):
        """执行条件节点"""
        if not node.condition:
            raise ValueError("条件节点未设置条件函数")
        
        # 评估条件
        condition_result = node.condition(instance.variables)
        
        node.result = {"condition_result": condition_result}
        
        # 根据条件结果决定下一个节点
        if condition_result:
            next_node = node.on_success
        else:
            next_node = node.on_failure
        
        if next_node:
            # 直接跳转到下一个节点，不通过正常的流程
            # 这里需要在调用方处理
            pass
    
    async def _execute_parallel_node(
        self,
        instance: WorkflowInstance,
        workflow: WorkflowDefinition,
        node: WorkflowNode
    ):
        """执行并行节点"""
        if not node.parallel_nodes:
            raise ValueError("并行节点未设置并行子节点")
        
        # 并行执行所有子节点
        tasks = []
        for sub_node_id in node.parallel_nodes:
            tasks.append(self._execute_node(instance, workflow, sub_node_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        node.result = {
            "parallel_results": [
                {"node_id": sub_node_id, "result": str(r) if isinstance(r, Exception) else r}
                for sub_node_id, r in zip(node.parallel_nodes, results)
            ]
        }
    
    async def _execute_loop_node(
        self,
        instance: WorkflowInstance,
        workflow: WorkflowDefinition,
        node: WorkflowNode
    ):
        """执行循环节点"""
        loop_results = []
        
        for i in range(node.loop_count):
            # 设置循环变量
            if node.loop_variable:
                instance.variables[node.loop_variable] = i
            
            # 执行循环体（假设循环体是下一个节点）
            if node.next_nodes:
                loop_node_id = node.next_nodes[0]
                await self._execute_node(instance, workflow, loop_node_id)
                
                loop_results.append({
                    "iteration": i,
                    "result": instance.node_results.get(loop_node_id)
                })
        
        node.result = {
            "loop_count": node.loop_count,
            "results": loop_results
        }
    
    def _get_next_node(self, node: WorkflowNode, success: bool = True) -> Optional[str]:
        """获取下一个节点
        
        Args:
            node: 当前节点
            success: 是否成功
            
        Returns:
            下一个节点ID，如果没有则返回None
        """
        if success and node.on_success:
            return node.on_success
        elif not success and node.on_failure:
            return node.on_failure
        elif node.next_nodes:
            return node.next_nodes[0]
        else:
            return None
    
    def get_workflow_status(self, instance_id: str) -> Dict[str, Any]:
        """获取工作流实例状态
        
        Args:
            instance_id: 实例ID
            
        Returns:
            状态信息
        """
        if instance_id not in self.instances:
            raise ValueError(f"工作流实例不存在: {instance_id}")
        
        instance = self.instances[instance_id]
        workflow = self.workflows[instance.workflow_id]
        
        return {
            "instance_id": instance.instance_id,
            "workflow_name": workflow.name,
            "status": instance.status.value,
            "current_node": instance.current_node_id,
            "progress": self._calculate_progress(instance, workflow),
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "error": instance.error,
            "node_results": instance.node_results
        }
    
    def _calculate_progress(
        self,
        instance: WorkflowInstance,
        workflow: WorkflowDefinition
    ) -> float:
        """计算工作流进度"""
        total_nodes = len(workflow.nodes)
        if total_nodes == 0:
            return 0.0
        
        completed_nodes = sum(
            1 for node_id in instance.node_results
            if node_id in workflow.nodes
        )
        
        return (completed_nodes / total_nodes) * 100
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有工作流"""
        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "version": wf.version,
                "node_count": len(wf.nodes),
                "created_at": wf.created_at.isoformat()
            }
            for wf in self.workflows.values()
        ]
    
    def list_instances(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出工作流实例
        
        Args:
            workflow_id: 可选的工作流ID过滤
            
        Returns:
            实例列表
        """
        instances = self.instances.values()
        
        if workflow_id:
            instances = [inst for inst in instances if inst.workflow_id == workflow_id]
        
        return [
            {
                "instance_id": inst.instance_id,
                "workflow_id": inst.workflow_id,
                "name": inst.name,
                "status": inst.status.value,
                "created_at": inst.created_at.isoformat(),
                "completed_at": inst.completed_at.isoformat() if inst.completed_at else None
            }
            for inst in instances
        ]
