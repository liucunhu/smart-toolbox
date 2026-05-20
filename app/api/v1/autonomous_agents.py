"""
自主智能体 API端点
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.services.agents.autonomous_agents import (
    GoalDecomposer, UncertaintyHandler, LongTermPlanner,
    ReinforcementLearner, RewardCalculator, PolicyOptimizer,
    TaskGoal
)
from app.services.agents.cross_platform_learning import (
    CrossPlatformKnowledgeBase, PlatformAdapter, TransferLearningEngine
)
from app.services.agents.task_execution_engine import execution_engine
from app.services.agents.workflow_orchestrator import get_workflow_orchestrator
from app.services.agents.adaptive_learning import adaptive_learning_engine
import uuid
from datetime import datetime

router = APIRouter(prefix="/agents/autonomous", tags=["自主智能体"])


# ==================== Pydantic Models ====================

class GoalDecomposeRequest(BaseModel):
    description: str
    priority: int = 5
    constraints: Optional[Dict[str, Any]] = None


class UncertaintyAssessRequest(BaseModel):
    context: Dict[str, Any]


class LongTermPlanRequest(BaseModel):
    objectives: List[str]
    current_state: Dict[str, Any]


class QLearningUpdateRequest(BaseModel):
    state: str
    action: str
    reward: float
    next_state: str


class ActionChooseRequest(BaseModel):
    state: str
    available_actions: List[str]


class RewardCalculateRequest(BaseModel):
    outcome: Dict[str, Any]
    metrics: Dict[str, Any]


class KnowledgeAddRequest(BaseModel):
    platform: str
    knowledge_type: str
    content: Dict[str, Any]
    confidence: float = 1.0


class KnowledgeTransferRequest(BaseModel):
    source_platform: str
    target_platform: str
    knowledge_type: str


class PlatformLearnRequest(BaseModel):
    platform: str
    experience_data: List[Dict[str, Any]]


class ApplyToPlatformRequest(BaseModel):
    source_platform: str
    target_platform: str
    task_context: Dict[str, Any]


# ==================== 实例化服务 ====================

goal_decomposer = GoalDecomposer()
uncertainty_handler = UncertaintyHandler()
long_term_planner = LongTermPlanner()
rl_learner = ReinforcementLearner()
reward_calculator = RewardCalculator()
policy_optimizer = PolicyOptimizer()
transfer_engine = TransferLearningEngine()


# ==================== 任务规划API ====================

@router.post("/planning/decompose", summary="分解目标")
def decompose_goal(request: GoalDecomposeRequest):
    """将模糊目标分解为具体任务"""
    goal = TaskGoal(
        goal_id=str(uuid.uuid4()),
        description=request.description,
        priority=request.priority,
        constraints=request.constraints or {}
    )
    
    tasks = goal_decomposer.decompose_goal(goal)
    
    return {
        "status": "success",
        "goal_id": goal.goal_id,
        "tasks": [
            {
                "task_id": t.task_id,
                "description": t.description,
                "agent_type": t.agent_type,
                "priority": t.priority,
                "dependencies": t.dependencies
            }
            for t in tasks
        ]
    }


@router.post("/planning/assess-uncertainty", summary="评估不确定性")
def assess_uncertainty(request: UncertaintyAssessRequest):
    """评估当前上下文的不确定性"""
    assessment = uncertainty_handler.assess_uncertainty(request.context)
    
    return {
        "status": "success",
        "assessment": assessment
    }


@router.post("/planning/long-term", summary="创建长期计划")
def create_long_term_plan(request: LongTermPlanRequest):
    """创建跨周期长期计划"""
    plan = long_term_planner.create_long_term_plan(
        objectives=request.objectives,
        current_state=request.current_state
    )
    
    return {
        "status": "success",
        "plan": plan
    }


# ==================== 强化学习API ====================

@router.post("/learning/update-q-value", summary="更新Q值")
def update_q_value(request: QLearningUpdateRequest):
    """更新强化学习Q值"""
    rl_learner.update_q_value(
        state=request.state,
        action=request.action,
        reward=request.reward,
        next_state=request.next_state
    )
    
    return {
        "status": "success",
        "message": "Q值已更新"
    }


@router.post("/learning/choose-action", summary="选择动作")
def choose_action(request: ActionChooseRequest):
    """基于Q-learning选择最优动作"""
    action = rl_learner.choose_action(
        state=request.state,
        available_actions=request.available_actions
    )
    
    q_values = {
        a: rl_learner.get_q_value(request.state, a)
        for a in request.available_actions
    }
    
    return {
        "status": "success",
        "chosen_action": action,
        "q_values": q_values,
        "exploration_rate": rl_learner.exploration_rate
    }


@router.post("/learning/calculate-reward", summary="计算奖励")
def calculate_reward(request: RewardCalculateRequest):
    """计算多维度奖励值"""
    reward = reward_calculator.calculate_reward(
        outcome=request.outcome,
        metrics=request.metrics
    )
    
    return {
        "status": "success",
        "reward": reward,
        "breakdown": {
            "outcome": request.outcome,
            "metrics": request.metrics
        }
    }


@router.post("/learning/decay-exploration", summary="衰减探索率")
def decay_exploration(decay_rate: float = 0.995):
    """衰减探索率"""
    old_rate = rl_learner.exploration_rate
    rl_learner.decay_exploration(decay_rate)
    new_rate = rl_learner.exploration_rate
    
    return {
        "status": "success",
        "old_exploration_rate": old_rate,
        "new_exploration_rate": new_rate
    }


@router.get("/learning/q-table", summary="获取Q表")
def get_q_table():
    """获取当前Q表"""
    return {
        "status": "success",
        "q_table_size": len(rl_learner.q_table),
        "states_count": len(rl_learner.states),
        "actions_count": len(rl_learner.actions)
    }


# ==================== 知识迁移API ====================

@router.post("/knowledge/add", summary="添加平台知识")
def add_knowledge(request: KnowledgeAddRequest):
    """向知识库添加平台特定知识"""
    transfer_engine.knowledge_base.add_knowledge(
        platform=request.platform,
        knowledge_type=request.knowledge_type,
        content=request.content,
        confidence=request.confidence
    )
    
    return {
        "status": "success",
        "message": f"已添加{request.platform}平台知识"
    }


@router.post("/knowledge/transfer", summary="迁移知识")
def transfer_knowledge(request: KnowledgeTransferRequest):
    """从源平台迁移知识到目标平台"""
    transferred = transfer_engine.knowledge_base.transfer_knowledge(
        source_platform=request.source_platform,
        target_platform=request.target_platform,
        knowledge_type=request.knowledge_type
    )
    
    if not transferred:
        return {
            "status": "success",
            "transferred": False,
            "message": "无可迁移的知识"
        }
    
    return {
        "status": "success",
        "transferred": True,
        "data": transferred
    }


@router.post("/knowledge/learn-from-platform", summary="从平台学习")
def learn_from_platform(request: PlatformLearnRequest):
    """从平台经验数据中学习"""
    transfer_engine.learn_from_platform(
        platform=request.platform,
        experience_data=request.experience_data
    )
    
    return {
        "status": "success",
        "message": f"已从{request.platform}平台学习"
    }


@router.post("/knowledge/apply-to-platform", summary="应用到平台")
def apply_to_platform(request: ApplyToPlatformRequest):
    """将源平台知识应用到目标平台"""
    result = transfer_engine.apply_to_platform(
        source_platform=request.source_platform,
        target_platform=request.target_platform,
        task_context=request.task_context
    )
    
    return {
        "status": "success",
        "result": result
    }


@router.get("/knowledge/statistics", summary="获取知识统计")
def get_knowledge_statistics():
    """获取知识迁移统计信息"""
    stats = transfer_engine.get_transfer_statistics()
    
    return {
        "status": "success",
        "statistics": stats
    }


@router.get("/knowledge/query", summary="查询平台知识")
def query_platform_knowledge(
    platform: str = Query(...),
    knowledge_type: Optional[str] = Query(None)
):
    """查询指定平台的知识"""
    knowledge_list = transfer_engine.knowledge_base.query_knowledge(
        platform=platform,
        knowledge_type=knowledge_type
    )
    
    return {
        "status": "success",
        "count": len(knowledge_list),
        "knowledge": [
            {
                "platform": k.platform,
                "knowledge_type": k.knowledge_type,
                "content": k.content,
                "confidence": k.confidence,
                "created_at": k.created_at.isoformat()
            }
            for k in knowledge_list
        ]
    }


# ==================== 任务执行 API (Phase 4) ====================

class TaskExecuteRequest(BaseModel):
    """任务执行请求"""
    agent_type: str
    task_params: Dict[str, Any]
    task_id: Optional[str] = None


@router.post("/execute", summary="执行任务")
async def execute_task(request: TaskExecuteRequest):
    """
    执行智能体任务
    
    - **agent_type**: 智能体类型
    - **task_params**: 任务参数
    - **task_id**: 任务ID（可选）
    """
    try:
        result = await execution_engine.execute_task(
            agent_type=request.agent_type,
            task_params=request.task_params,
            task_id=request.task_id or str(uuid.uuid4())
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务执行失败: {str(e)}")


@router.get("/execution/history", summary="获取任务执行历史")
def get_execution_history(limit: int = Query(50, ge=1, le=200)):
    """获取任务执行历史"""
    history = execution_engine.get_task_history(limit=limit)
    return {
        "status": "success",
        "count": len(history),
        "history": history
    }


@router.get("/execution/stats", summary="获取执行统计")
def get_execution_stats():
    """获取执行器统计信息"""
    stats = execution_engine.get_executor_stats()
    return {
        "status": "success",
        "stats": stats
    }


@router.get("/execution/executors", summary="获取已注册的执行器")
def get_registered_executors():
    """获取所有已注册的任务执行器"""
    executors_info = {}
    for agent_type in execution_engine.executors.keys():
        executors_info[agent_type] = {
            "agent_type": agent_type,
            "registered": True
        }
    
    return {
        "status": "success",
        "count": len(executors_info),
        "executors": executors_info
    }


# ==================== 工作流编排 API (Phase 5) ====================

class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求"""
    name: str
    description: str
    tasks: List[Dict[str, Any]]  # 分解后的任务列表


class ABTestCreateRequest(BaseModel):
    """A/B测试创建请求"""
    test_name: str
    variants: List[str]
    metric: str = "success_rate"


class ABTestRecordRequest(BaseModel):
    """A/B测试结果记录请求"""
    test_id: str
    variant: str
    result: Dict[str, Any]


@router.post("/workflow/execute", summary="执行工作流")
async def execute_workflow(request: WorkflowExecuteRequest):
    """
    执行工作流
    - **name**: 工作流名称
    - **description**: 描述
    - **tasks**: 任务列表
    """
    try:
        # 获取工作流编排器
        workflow_orchestrator = get_workflow_orchestrator(execution_engine)
        
        # 从任务构建工作流
        workflow = workflow_orchestrator.build_workflow_from_tasks(
            request.tasks,
            request.name
        )
        
        # 执行工作流
        result = await workflow_orchestrator.execute_workflow(workflow.workflow_id)
        
        return {
            "status": "success",
            "workflow_id": workflow.workflow_id,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@router.get("/workflow/{workflow_id}/status", summary="获取工作流状态")
def get_workflow_status(workflow_id: str):
    """获取工作流执行状态"""
    try:
        workflow_orchestrator = get_workflow_orchestrator(execution_engine)
        status = workflow_orchestrator.get_workflow_status(workflow_id)
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/workflow/list", summary="列出工作流")
def list_workflows(status: Optional[str] = Query(None)):
    """列出工作流"""
    try:
        workflow_orchestrator = get_workflow_orchestrator(execution_engine)
        workflows = workflow_orchestrator.list_workflows(status)
        return {
            "status": "success",
            "workflows": workflows
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 智能增强 API (Phase 6) ====================

@router.get("/learning/insights/{agent_type}", summary="获取学习洞察")
def get_learning_insights(agent_type: str):
    """获取特定智能体的学习洞察"""
    try:
        insights = adaptive_learning_engine.get_learning_insights(agent_type)
        return {
            "status": "success",
            "insights": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/record-execution", summary="记录执行经验")
def record_execution(
    agent_type: str = Query(...),
    task_params: str = Query(...),  # JSON字符串
    result: str = Query(...),      # JSON字符串
    duration: float = Query(...)
):
    """记录智能体执行经验"""
    try:
        # 解析JSON字符串
        import json
        parsed_task_params = json.loads(task_params)
        parsed_result = json.loads(result)
        
        adaptive_learning_engine.record_execution(
            agent_type, parsed_task_params, parsed_result, duration
        )
        
        return {
            "status": "success",
            "message": "执行经验已记录"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/ab-test/create", summary="创建A/B测试")
def create_ab_test(request: ABTestCreateRequest):
    """创建A/B测试"""
    try:
        test_id = adaptive_learning_engine.ab_test_manager.create_test(
            request.test_name, request.variants, request.metric
        )
        return {
            "status": "success",
            "test_id": test_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test/{test_id}/assign", summary="分配测试变体")
def assign_ab_variant(test_id: str):
    """为用户分配A/B测试变体"""
    try:
        variant = adaptive_learning_engine.ab_test_manager.assign_variant(test_id)
        return {
            "status": "success",
            "variant": variant
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test/record-result", summary="记录测试结果")
def record_ab_result(request: ABTestRecordRequest):
    """记录A/B测试结果"""
    try:
        adaptive_learning_engine.ab_test_manager.record_result(
            request.test_id, request.variant, request.result
        )
        return {
            "status": "success",
            "message": "结果已记录"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test/{test_id}/analyze", summary="分析A/B测试")
def analyze_ab_test(test_id: str):
    """分析A/B测试结果"""
    try:
        analysis = adaptive_learning_engine.ab_test_manager.analyze_test(test_id)
        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/performance/{agent_type}", summary="获取性能分析")
def get_performance_analytics(agent_type: str):
    """获取智能体性能分析"""
    try:
        report = adaptive_learning_engine.performance_analyzer.get_performance_report(agent_type)
        return {
            "status": "success",
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/suggestions/{agent_type}", summary="获取优化建议")
def get_optimization_suggestions(agent_type: str):
    """获取智能体优化建议"""
    try:
        suggestions = adaptive_learning_engine.performance_analyzer.get_optimization_suggestions(agent_type)
        return {
            "status": "success",
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/recommend-strategy", summary="推荐策略")
def recommend_strategy(
    agent_type: str = Query(...),
    context: str = Query(...)  # JSON字符串
):
    """推荐最优策略"""
    try:
        import json
        parsed_context = json.loads(context)
        
        recommendation = adaptive_learning_engine.recommend_strategy(agent_type, parsed_context)
        return {
            "status": "success",
            "recommendation": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
