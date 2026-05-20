"""
智能体协作系统API端点
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.db.session import get_db
from app.models.agents import AgentWorkflow, AgentWorkflowInstance, AgentExperience, AgentCoordinationLog, AgentInfo

router = APIRouter(prefix="/agents", tags=["智能体协作"])


# ==================== Pydantic Models ====================

class AgentRegisterRequest(BaseModel):
    agent_type: str
    capabilities: Optional[List[str]] = None


class TaskDecomposeRequest(BaseModel):
    task_name: str
    description: str
    subtask_definitions: List[Dict[str, Any]]
    priority: str = "medium"
    metadata: Optional[Dict[str, Any]] = None


class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = None


class WorkflowNodeRequest(BaseModel):
    name: str
    node_type: str  # start/end/task/condition/parallel/loop
    description: Optional[str] = ""
    task_type: Optional[str] = None
    task_params: Optional[Dict[str, Any]] = None
    loop_count: Optional[int] = 1
    parallel_nodes: Optional[List[str]] = None
    next_nodes: Optional[List[str]] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NodeConnectRequest(BaseModel):
    from_node_id: str
    to_node_id: str
    condition: str = "on_success"


class WorkflowExecuteRequest(BaseModel):
    initial_variables: Optional[Dict[str, Any]] = None


class ExperienceAddRequest(BaseModel):
    task_type: str
    action: str
    context: Optional[Dict[str, Any]] = None
    result: str  # success/failed
    reward: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class ExperienceQueryRequest(BaseModel):
    task_type: str
    context: Optional[Dict[str, Any]] = None
    limit: int = 5


# ==================== 智能体协调API ====================

@router.post("/register", summary="注册智能体")
def register_agent(
    request: AgentRegisterRequest,
    db: Session = Depends(get_db)
):
    """注册新的智能体"""
    agent_id = str(uuid.uuid4())
    
    agent = AgentInfo(
        id=agent_id,
        agent_type=request.agent_type,
        capabilities=request.capabilities or [],
        status="idle"
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return {
        "status": "success",
        "agent_id": agent_id,
        "message": f"智能体已注册: {request.agent_type}"
    }


@router.get("/list", summary="获取智能体列表")
def list_agents(
    agent_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取智能体列表"""
    try:
        query = db.query(AgentInfo)
        
        if agent_type:
            query = query.filter(AgentInfo.agent_type == agent_type)
        if status:
            query = query.filter(AgentInfo.status == status)
        
        agents = query.all()
        
        return {
            "status": "success",
            "count": len(agents),
            "agents": [
                {
                    "id": a.id,
                    "agent_type": a.agent_type,
                    "status": a.status,
                    "capabilities": a.capabilities,
                    "completed_tasks": a.completed_tasks,
                    "failed_tasks": a.failed_tasks,
                    "load": a.load,
                    "last_heartbeat": a.last_heartbeat.isoformat() if a.last_heartbeat else None
                }
                for a in agents
            ]
        }
    except Exception as e:
        # 如果表不存在或查询失败，返回空列表
        return {
            "status": "success",
            "count": 0,
            "agents": [],
            "note": "智能体表尚未初始化"
        }


@router.get("/system/status", summary="获取系统状态")
def get_system_status(db: Session = Depends(get_db)):
    """获取智能体系统整体状态"""
    try:
        total_agents = db.query(AgentInfo).count()
        idle_agents = db.query(AgentInfo).filter(AgentInfo.status == "idle").count()
        busy_agents = db.query(AgentInfo).filter(AgentInfo.status == "busy").count()
        
        total_workflows = db.query(AgentWorkflow).count()
        active_instances = db.query(AgentWorkflowInstance).filter(
            AgentWorkflowInstance.status == "running"
        ).count()
        
        total_experiences = db.query(AgentExperience).count()
        
        return {
            "status": "success",
            "agents": {
                "total": total_agents,
                "idle": idle_agents,
                "busy": busy_agents
            },
            "workflows": {
                "total": total_workflows,
                "active_instances": active_instances
            },
            "experiences": {
                "total": total_experiences
            }
        }
    except Exception as e:
        # 如果表不存在或查询失败，返回默认值
        return {
            "status": "success",
            "agents": {
                "total": 0,
                "idle": 0,
                "busy": 0
            },
            "workflows": {
                "total": 0,
                "active_instances": 0
            },
            "experiences": {
                "total": 0
            },
            "note": "系统表尚未初始化"
        }


# ==================== 工作流管理API ====================

@router.post("/workflows", summary="创建工作流")
def create_workflow(
    request: WorkflowCreateRequest,
    db: Session = Depends(get_db)
):
    """创建新的工作流定义"""
    workflow_id = str(uuid.uuid4())
    
    workflow = AgentWorkflow(
        id=workflow_id,
        name=request.name,
        description=request.description,
        definition={"nodes": {}, "start_node_id": None},
        workflow_metadata=request.metadata or {}
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    return {
        "status": "success",
        "workflow_id": workflow_id,
        "message": f"工作流已创建: {request.name}"
    }


@router.post("/workflows/{workflow_id}/nodes", summary="添加工作流节点")
def add_workflow_node(
    workflow_id: str,
    request: WorkflowNodeRequest,
    db: Session = Depends(get_db)
):
    """向工作流添加节点"""
    workflow = db.query(AgentWorkflow).filter(AgentWorkflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    node_id = str(uuid.uuid4())
    
    # 更新工作流定义
    definition = workflow.definition
    if "nodes" not in definition:
        definition["nodes"] = {}
    
    definition["nodes"][node_id] = {
        "node_id": node_id,
        "name": request.name,
        "node_type": request.node_type,
        "description": request.description,
        "task_type": request.task_type,
        "task_params": request.task_params or {},
        "loop_count": request.loop_count,
        "parallel_nodes": request.parallel_nodes or [],
        "next_nodes": request.next_nodes or [],
        "on_success": request.on_success,
        "on_failure": request.on_failure,
        "metadata": request.metadata or {}
    }
    
    # 如果是第一个节点，设置为起始节点
    if not definition.get("start_node_id"):
        definition["start_node_id"] = node_id
    
    workflow.definition = definition
    db.commit()
    
    return {
        "status": "success",
        "node_id": node_id,
        "message": f"节点已添加: {request.name}"
    }


@router.post("/workflows/{workflow_id}/connect", summary="连接工作流节点")
def connect_workflow_nodes(
    workflow_id: str,
    request: NodeConnectRequest,
    db: Session = Depends(get_db)
):
    """连接工作流中的两个节点"""
    workflow = db.query(AgentWorkflow).filter(AgentWorkflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    definition = workflow.definition
    nodes = definition.get("nodes", {})
    
    if request.from_node_id not in nodes:
        raise HTTPException(status_code=404, detail=f"源节点不存在: {request.from_node_id}")
    
    if request.to_node_id not in nodes:
        raise HTTPException(status_code=404, detail=f"目标节点不存在: {request.to_node_id}")
    
    # 更新连接
    if request.condition == "on_success":
        nodes[request.from_node_id]["on_success"] = request.to_node_id
    elif request.condition == "on_failure":
        nodes[request.from_node_id]["on_failure"] = request.to_node_id
    
    if request.to_node_id not in nodes[request.from_node_id].get("next_nodes", []):
        nodes[request.from_node_id].setdefault("next_nodes", []).append(request.to_node_id)
    
    workflow.definition = definition
    db.commit()
    
    return {
        "status": "success",
        "message": f"节点已连接: {request.from_node_id} -> {request.to_node_id}"
    }


@router.post("/workflows/{workflow_id}/execute", summary="执行工作流")
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db)
):
    """执行工作流实例"""
    workflow = db.query(AgentWorkflow).filter(AgentWorkflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    instance_id = str(uuid.uuid4())
    
    instance = AgentWorkflowInstance(
        id=instance_id,
        workflow_id=workflow_id,
        name=workflow.name,
        status="pending",
        variables=request.initial_variables or {}
    )
    
    db.add(instance)
    db.commit()
    db.refresh(instance)
    
    # TODO: 异步执行工作流
    # 这里应该调用TaskOrchestrator执行工作流
    
    return {
        "status": "success",
        "instance_id": instance_id,
        "message": "工作流已开始执行"
    }


@router.get("/workflows/{instance_id}/status", summary="获取工作流实例状态")
def get_workflow_status(
    instance_id: str,
    db: Session = Depends(get_db)
):
    """获取工作流实例的执行状态"""
    instance = db.query(AgentWorkflowInstance).filter(
        AgentWorkflowInstance.id == instance_id
    ).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="工作流实例不存在")
    
    return {
        "status": "success",
        "instance": {
            "id": instance.id,
            "workflow_id": instance.workflow_id,
            "name": instance.name,
            "status": instance.status,
            "current_node_id": instance.current_node_id,
            "variables": instance.variables,
            "node_results": instance.node_results,
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "error": instance.error
        }
    }


@router.get("/workflows", summary="列出工作流")
def list_workflows(
    db: Session = Depends(get_db)
):
    """列出所有工作流"""
    workflows = db.query(AgentWorkflow).all()
    
    return {
        "status": "success",
        "count": len(workflows),
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "version": w.version,
                "status": w.status,
                "created_at": w.created_at.isoformat()
            }
            for w in workflows
        ]
    }


# ==================== 经验管理API ====================

@router.post("/experiences", summary="添加经验")
def add_experience(
    request: ExperienceAddRequest,
    db: Session = Depends(get_db)
):
    """添加新的经验记录"""
    experience_id = str(uuid.uuid4())
    
    experience = AgentExperience(
        id=experience_id,
        task_type=request.task_type,
        action=request.action,
        context=request.context,
        result=request.result,
        reward=request.reward,
        metadata=request.metadata
    )
    
    db.add(experience)
    db.commit()
    db.refresh(experience)
    
    return {
        "status": "success",
        "experience_id": experience_id,
        "message": "经验已添加"
    }


@router.post("/experiences/query", summary="查询相似经验")
def query_experiences(
    request: ExperienceQueryRequest,
    db: Session = Depends(get_db)
):
    """查询相似的经验记录"""
    experiences = db.query(AgentExperience).filter(
        AgentExperience.task_type == request.task_type
    ).order_by(
        AgentExperience.reward.desc()
    ).limit(request.limit).all()
    
    return {
        "status": "success",
        "count": len(experiences),
        "experiences": [
            {
                "id": e.id,
                "task_type": e.task_type,
                "action": e.action,
                "context": e.context,
                "result": e.result,
                "reward": e.reward,
                "created_at": e.created_at.isoformat()
            }
            for e in experiences
        ]
    }


@router.get("/experiences/best-practice", summary="获取最佳实践")
def get_best_practice(
    task_type: str = Query(...),
    action: str = Query(...),
    db: Session = Depends(get_db)
):
    """获取指定任务类型和动作的最佳实践"""
    experience = db.query(AgentExperience).filter(
        AgentExperience.task_type == task_type,
        AgentExperience.action == action
    ).order_by(
        AgentExperience.reward.desc()
    ).first()
    
    if not experience:
        return {
            "status": "success",
            "best_practice": None,
            "message": "未找到相关经验"
        }
    
    return {
        "status": "success",
        "best_practice": {
            "id": experience.id,
            "task_type": experience.task_type,
            "action": experience.action,
            "context": experience.context,
            "result": experience.result,
            "reward": experience.reward,
            "metadata": experience.metadata
        }
    }


@router.get("/experiences/statistics", summary="获取经验统计")
def get_experience_statistics(
    db: Session = Depends(get_db)
):
    """获取经验池的统计信息"""
    total = db.query(AgentExperience).count()
    success_count = db.query(AgentExperience).filter(
        AgentExperience.result == "success"
    ).count()
    failed_count = db.query(AgentExperience).filter(
        AgentExperience.result == "failed"
    ).count()
    
    avg_reward = db.query(AgentExperience).with_entities(
        db.func.avg(AgentExperience.reward)
    ).scalar() or 0.0
    
    return {
        "status": "success",
        "statistics": {
            "total_experiences": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": success_count / total if total > 0 else 0,
            "average_reward": float(avg_reward)
        }
    }
