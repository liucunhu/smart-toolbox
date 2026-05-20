"""
自主智能体 - 任务规划与强化学习引擎
"""
import asyncio
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import math

logger = logging.getLogger(__name__)


# ==================== 任务规划器 ====================

@dataclass
class TaskGoal:
    """任务目标"""
    goal_id: str
    description: str
    priority: int  # 1-10
    constraints: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Optional[str] = None
    deadline: Optional[datetime] = None


@dataclass
class PlannedTask:
    """规划后的任务"""
    task_id: str
    goal_id: str
    description: str
    agent_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    estimated_duration: float = 0.0  # 预计执行时长（秒）
    priority: int = 5


class GoalDecomposer:
    """目标分解引擎 - 将模糊需求转化为具体任务"""
    
    def __init__(self):
        self.decomposition_patterns = {
            "content_creation": [
                {"step": "topic_research", "agent_type": "research"},
                {"step": "outline_generation", "agent_type": "planning"},
                {"step": "content_writing", "agent_type": "content_generation"},
                {"step": "compliance_check", "agent_type": "compliance_check"},
                {"step": "image_generation", "agent_type": "image_generation"},
                {"step": "publish", "agent_type": "distribution"}
            ],
            "account_nurturing": [
                {"step": "browse_videos", "agent_type": "nurturing"},
                {"step": "interact", "agent_type": "nurturing"},
                {"step": "follow_accounts", "agent_type": "nurturing"}
            ]
        }
    
    def decompose_goal(self, goal: TaskGoal) -> List[PlannedTask]:
        """分解目标为具体任务
        
        Args:
            goal: 任务目标
            
        Returns:
            规划后的任务列表
        """
        logger.info(f"分解目标: {goal.description}")
        
        # 根据目标描述识别任务类型
        task_type = self._identify_task_type(goal.description)
        
        if task_type in self.decomposition_patterns:
            pattern = self.decomposition_patterns[task_type]
            return self._create_tasks_from_pattern(goal, pattern)
        else:
            # 通用分解策略
            return self._generic_decomposition(goal)
    
    def _identify_task_type(self, description: str) -> str:
        """识别任务类型"""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["文章", "内容", "创作", "发布"]):
            return "content_creation"
        elif any(keyword in description_lower for keyword in ["养号", "账号", "活跃"]):
            return "account_nurturing"
        else:
            return "generic"
    
    def _create_tasks_from_pattern(self, goal: TaskGoal, pattern: List[Dict]) -> List[PlannedTask]:
        """根据模式创建任务"""
        tasks = []
        previous_task_id = None
        
        for i, step in enumerate(pattern):
            task_id = str(uuid.uuid4())
            
            task = PlannedTask(
                task_id=task_id,
                goal_id=goal.goal_id,
                description=f"{goal.description} - {step['step']}",
                agent_type=step['agent_type'],
                priority=goal.priority,
                dependencies=[previous_task_id] if previous_task_id else []
            )
            
            tasks.append(task)
            previous_task_id = task_id
        
        return tasks
    
    def _generic_decomposition(self, goal: TaskGoal) -> List[PlannedTask]:
        """通用分解策略"""
        # 创建一个通用任务，使用 content_generation 执行器
        task_id = str(uuid.uuid4())
        
        task = PlannedTask(
            task_id=task_id,
            goal_id=goal.goal_id,
            description=goal.description,
            agent_type="content_generation",  # 使用已注册的内容生成执行器
            priority=goal.priority
        )
        
        return [task]


class UncertaintyHandler:
    """不确定性处理器 - 处理信息不完整的情况"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def assess_uncertainty(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """评估不确定性
        
        Args:
            context: 上下文信息
            
        Returns:
            不确定性评估结果
        """
        missing_info = self._identify_missing_information(context)
        confidence = self._calculate_confidence(context, missing_info)
        
        return {
            "missing_information": missing_info,
            "confidence": confidence,
            "recommendation": self._get_recommendation(confidence, missing_info)
        }
    
    def _identify_missing_information(self, context: Dict[str, Any]) -> List[str]:
        """识别缺失的信息"""
        required_fields = ["platform", "account_id", "content_type"]
        missing = [field for field in required_fields if field not in context]
        return missing
    
    def _calculate_confidence(self, context: Dict[str, Any], missing: List[str]) -> float:
        """计算置信度"""
        total_fields = 10  # 假设总共有10个重要字段
        available_fields = len(context)
        confidence = available_fields / total_fields
        
        # 如果有必需字段缺失，大幅降低置信度
        if missing:
            confidence *= 0.5
        
        return min(1.0, confidence)
    
    def _get_recommendation(self, confidence: float, missing: List[str]) -> str:
        """获取建议"""
        if confidence >= self.confidence_threshold:
            return "proceed"
        elif missing:
            return f"need_more_info: {', '.join(missing)}"
        else:
            return "caution"


class LongTermPlanner:
    """长期规划器 - 制定跨周期策略"""
    
    def __init__(self):
        self.planning_horizon = 30  # 规划周期（天）
    
    def create_long_term_plan(
        self,
        objectives: List[str],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建长期计划
        
        Args:
            objectives: 目标列表
            current_state: 当前状态
            
        Returns:
            长期计划
        """
        milestones = self._generate_milestones(objectives)
        weekly_plans = self._create_weekly_plans(milestones, current_state)
        
        return {
            "objectives": objectives,
            "planning_horizon_days": self.planning_horizon,
            "milestones": milestones,
            "weekly_plans": weekly_plans,
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_milestones(self, objectives: List[str]) -> List[Dict[str, Any]]:
        """生成里程碑"""
        milestones = []
        
        for i, objective in enumerate(objectives):
            milestone = {
                "id": str(uuid.uuid4()),
                "objective": objective,
                "target_day": (i + 1) * 7,  # 每周一个里程碑
                "description": f"完成目标: {objective}",
                "success_criteria": "达到预期指标"
            }
            milestones.append(milestone)
        
        return milestones
    
    def _create_weekly_plans(
        self,
        milestones: List[Dict],
        current_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """创建周计划"""
        weekly_plans = []
        
        for week in range(1, 5):  # 4周计划
            plan = {
                "week": week,
                "focus": f"第{week}周重点任务",
                "tasks": [],
                "expected_outcomes": []
            }
            
            # 根据里程碑分配任务
            for milestone in milestones:
                if milestone["target_day"] <= week * 7:
                    plan["tasks"].append({
                        "type": "milestone_task",
                        "description": milestone["description"],
                        "priority": "high"
                    })
            
            weekly_plans.append(plan)
        
        return weekly_plans


# ==================== 强化学习引擎 ====================

class ReinforcementLearner:
    """强化学习引擎 - Q-Learning实现"""
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9, exploration_rate: float = 0.1):
        self.learning_rate = learning_rate  # 学习率 alpha
        self.discount_factor = discount_factor  # 折扣因子 gamma
        self.exploration_rate = exploration_rate  # 探索率 epsilon
        
        # Q表: state -> action -> value
        self.q_table: Dict[str, Dict[str, float]] = {}
        
        # 状态和动作空间
        self.states: set = set()
        self.actions: set = set()
    
    def get_q_value(self, state: str, action: str) -> float:
        """获取Q值"""
        if state not in self.q_table:
            self.q_table[state] = {}
        return self.q_table[state].get(action, 0.0)
    
    def update_q_value(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str
    ):
        """更新Q值
        
        Q(s,a) = Q(s,a) + alpha * [reward + gamma * max(Q(s',a')) - Q(s,a)]
        """
        if state not in self.q_table:
            self.q_table[state] = {}
        
        if next_state not in self.q_table:
            self.q_table[next_state] = {}
        
        # 当前Q值
        current_q = self.q_table[state].get(action, 0.0)
        
        # 下一个状态的最大Q值
        max_next_q = max(self.q_table[next_state].values()) if self.q_table[next_state] else 0.0
        
        # Q-learning更新公式
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
        
        logger.debug(f"Q值更新: {state}/{action} = {new_q:.4f} (reward={reward})")
    
    def choose_action(self, state: str, available_actions: List[str]) -> str:
        """选择动作（epsilon-greedy策略）"""
        # 探索：随机选择动作
        if random.random() < self.exploration_rate:
            return random.choice(available_actions)
        
        # 利用：选择Q值最大的动作
        if state not in self.q_table or not self.q_table[state]:
            return random.choice(available_actions)
        
        # 过滤出可用动作的Q值
        q_values = {
            action: self.q_table[state].get(action, 0.0)
            for action in available_actions
        }
        
        # 返回Q值最大的动作
        return max(q_values, key=q_values.get)
    
    def decay_exploration(self, decay_rate: float = 0.995):
        """衰减探索率"""
        self.exploration_rate *= decay_rate
        self.exploration_rate = max(0.01, self.exploration_rate)  # 最小探索率0.01
    
    def get_policy(self, state: str) -> Dict[str, float]:
        """获取策略（某状态下各动作的概率）"""
        if state not in self.q_table:
            return {}
        
        q_values = self.q_table[state]
        total = sum(q_values.values())
        
        if total == 0:
            # 均匀分布
            return {action: 1.0/len(q_values) for action in q_values}
        
        # 按Q值比例分配概率
        return {action: q/total for action, q in q_values.items()}


class RewardCalculator:
    """奖励计算器 - 多维度奖励评估"""
    
    def __init__(self):
        self.reward_weights = {
            "success": 1.0,
            "efficiency": 0.3,
            "quality": 0.5,
            "cost": -0.2
        }
    
    def calculate_reward(
        self,
        outcome: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> float:
        """计算奖励值
        
        Args:
            outcome: 执行结果
            metrics: 性能指标
            
        Returns:
            奖励值（-1到1）
        """
        reward = 0.0
        
        # 成功奖励
        if outcome.get("success", False):
            reward += self.reward_weights["success"]
        else:
            reward -= self.reward_weights["success"]
        
        # 效率奖励（越快越好）
        duration = metrics.get("duration", 0)
        if duration > 0:
            efficiency_score = max(0, 1.0 - (duration / 300))  # 5分钟内完成得满分
            reward += self.reward_weights["efficiency"] * efficiency_score
        
        # 质量奖励
        quality_score = metrics.get("quality_score", 0.5)
        reward += self.reward_weights["quality"] * quality_score
        
        # 成本惩罚
        cost = metrics.get("cost", 0)
        if cost > 0:
            cost_penalty = min(1.0, cost / 100)  # 成本超过100则完全惩罚
            reward += self.reward_weights["cost"] * cost_penalty
        
        # 限制在[-1, 1]范围
        return max(-1.0, min(1.0, reward))


class PolicyOptimizer:
    """策略优化器 - 持续改进行为策略"""
    
    def __init__(self):
        self.policy_history: List[Dict[str, Any]] = []
        self.improvement_threshold = 0.05
    
    def record_policy_performance(
        self,
        policy_id: str,
        performance: Dict[str, Any]
    ):
        """记录策略性能"""
        record = {
            "policy_id": policy_id,
            "performance": performance,
            "timestamp": datetime.now().isoformat()
        }
        
        self.policy_history.append(record)
        
        # 保持历史记录大小
        if len(self.policy_history) > 1000:
            self.policy_history = self.policy_history[-1000:]
    
    def analyze_improvement(self, policy_id: str) -> Dict[str, Any]:
        """分析策略改进情况"""
        policy_records = [
            r for r in self.policy_history
            if r["policy_id"] == policy_id
        ]
        
        if len(policy_records) < 2:
            return {
                "improved": False,
                "message": "数据不足，无法分析"
            }
        
        # 比较最近两次性能
        recent = policy_records[-1]["performance"]
        previous = policy_records[-2]["performance"]
        
        improvement = recent.get("reward", 0) - previous.get("reward", 0)
        
        return {
            "improved": improvement > self.improvement_threshold,
            "improvement": improvement,
            "current_reward": recent.get("reward", 0),
            "previous_reward": previous.get("reward", 0)
        }
    
    def suggest_optimization(self, policy_id: str) -> List[str]:
        """建议优化方向"""
        analysis = self.analyze_improvement(policy_id)
        
        suggestions = []
        
        if not analysis.get("improved", False):
            suggestions.append("增加探索率以发现更好的策略")
            suggestions.append("调整奖励权重配置")
            suggestions.append("考虑使用更复杂的状态表示")
        
        return suggestions
