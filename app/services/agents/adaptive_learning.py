"""
智能体自主学习和优化系统 - Phase 6
包括：自主学习、策略优化、A/B测试、性能分析
"""
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class ExperienceBuffer:
    """经验缓冲区 - 存储智能体的执行经验"""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.experiences: List[Dict[str, Any]] = []
    
    def add_experience(self, experience: Dict[str, Any]):
        """添加经验"""
        if len(self.experiences) >= self.capacity:
            self.experiences.pop(0)  # 移除最旧的经验
        
        experience["timestamp"] = datetime.now().isoformat()
        self.experiences.append(experience)
    
    def get_recent_experiences(self, count: int = 100) -> List[Dict[str, Any]]:
        """获取最近的经验"""
        return self.experiences[-count:]
    
    def get_experiences_by_agent(self, agent_type: str) -> List[Dict[str, Any]]:
        """获取特定智能体的经验"""
        return [exp for exp in self.experiences if exp.get("agent_type") == agent_type]
    
    def get_success_rate(self, agent_type: str = None) -> float:
        """计算成功率"""
        experiences = self.get_experiences_by_agent(agent_type) if agent_type else self.experiences
        
        if not experiences:
            return 0.0
        
        success_count = sum(1 for exp in experiences if exp.get("success", False))
        return success_count / len(experiences)


class ABTestManager:
    """A/B测试管理器"""
    
    def __init__(self):
        self.tests: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_test(self, test_name: str, variants: List[str], 
                    metric: str = "success_rate") -> str:
        """创建A/B测试"""
        test_id = f"test_{len(self.tests) + 1}"
        
        self.tests[test_id] = {
            "test_id": test_id,
            "name": test_name,
            "variants": variants,
            "metric": metric,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "assignments": defaultdict(int)  #  variant -> count
        }
        
        self.results[test_id] = []
        
        logger.info(f"创建A/B测试: {test_name} ({test_id})")
        return test_id
    
    def assign_variant(self, test_id: str) -> str:
        """分配变体（随机分配）"""
        if test_id not in self.tests:
            raise ValueError(f"测试不存在: {test_id}")
        
        test = self.tests[test_id]
        variant = random.choice(test["variants"])
        test["assignments"][variant] += 1
        
        return variant
    
    def record_result(self, test_id: str, variant: str, result: Dict[str, Any]):
        """记录测试结果"""
        if test_id not in self.results:
            raise ValueError(f"测试不存在: {test_id}")
        
        self.results[test_id].append({
            "variant": variant,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """分析测试结果"""
        if test_id not in self.tests:
            raise ValueError(f"测试不存在: {test_id}")
        
        test = self.tests[test_id]
        results = self.results[test_id]
        
        # 按变体分组统计
        variant_stats = defaultdict(lambda: {"count": 0, "success": 0, "total_metric": 0})
        
        for result in results:
            variant = result["variant"]
            variant_stats[variant]["count"] += 1
            
            if result["result"].get("success", False):
                variant_stats[variant]["success"] += 1
            
            # 累加指标值
            metric_value = result["result"].get(test["metric"], 0)
            variant_stats[variant]["total_metric"] += metric_value
        
        # 计算每个变体的平均表现
        analysis = {}
        for variant, stats in variant_stats.items():
            analysis[variant] = {
                "count": stats["count"],
                "success_rate": stats["success"] / stats["count"] if stats["count"] > 0 else 0,
                "avg_metric": stats["total_metric"] / stats["count"] if stats["count"] > 0 else 0
            }
        
        # 找出最佳变体
        best_variant = max(analysis.keys(), 
                          key=lambda v: analysis[v].get(test["metric"], 0)) if analysis else None
        
        return {
            "test_id": test_id,
            "name": test["name"],
            "status": test["status"],
            "total_samples": len(results),
            "variant_analysis": analysis,
            "best_variant": best_variant,
            "recommendation": f"建议使用变体 '{best_variant}'" if best_variant else "数据不足"
        }
    
    def stop_test(self, test_id: str):
        """停止测试"""
        if test_id in self.tests:
            self.tests[test_id]["status"] = "stopped"
            logger.info(f"A/B测试已停止: {test_id}")


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def record_metric(self, agent_type: str, metric_name: str, value: float, 
                      metadata: Dict[str, Any] = None):
        """记录性能指标"""
        record = {
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.metrics_history[f"{agent_type}_{metric_name}"].append(record)
        
        # 保持最近1000条记录
        key = f"{agent_type}_{metric_name}"
        if len(self.metrics_history[key]) > 1000:
            self.metrics_history[key] = self.metrics_history[key][-1000:]
    
    def get_performance_report(self, agent_type: str = None) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "agents": {}
        }
        
        # 按智能体类型分组
        agents = set()
        for key in self.metrics_history.keys():
            agent = key.split("_")[0]
            if agent_type and agent != agent_type:
                continue
            agents.add(agent)
        
        for agent in agents:
            agent_metrics = {}
            
            for key, records in self.metrics_history.items():
                if key.startswith(f"{agent}_"):
                    metric_name = key.replace(f"{agent}_", "")
                    
                    if records:
                        values = [r["value"] for r in records]
                        agent_metrics[metric_name] = {
                            "avg": sum(values) / len(values),
                            "min": min(values),
                            "max": max(values),
                            "latest": values[-1],
                            "samples": len(values)
                        }
            
            report["agents"][agent] = agent_metrics
        
        return report
    
    def get_optimization_suggestions(self, agent_type: str) -> List[Dict[str, str]]:
        """获取优化建议"""
        suggestions = []
        
        report = self.get_performance_report(agent_type)
        agent_data = report.get("agents", {}).get(agent_type, {})
        
        # 分析成功率
        if "success_rate" in agent_data:
            success_rate = agent_data["success_rate"]["avg"]
            if success_rate < 0.7:
                suggestions.append({
                    "type": "warning",
                    "message": f"成功率较低 ({success_rate:.1%})，建议检查任务参数和错误日志",
                    "priority": "high"
                })
            elif success_rate < 0.9:
                suggestions.append({
                    "type": "info",
                    "message": f"成功率良好 ({success_rate:.1%})，可以继续优化",
                    "priority": "medium"
                })
        
        # 分析执行时间
        if "duration" in agent_data:
            avg_duration = agent_data["duration"]["avg"]
            if avg_duration > 5:
                suggestions.append({
                    "type": "warning",
                    "message": f"平均执行时间较长 ({avg_duration:.2f}秒)，考虑优化算法或增加资源",
                    "priority": "high"
                })
        
        # 如果没有建议
        if not suggestions:
            suggestions.append({
                "type": "success",
                "message": "性能表现良好，继续保持",
                "priority": "low"
            })
        
        return suggestions


class AdaptiveLearningEngine:
    """自适应学习引擎 - 整合所有智能增强功能"""
    
    def __init__(self):
        self.experience_buffer = ExperienceBuffer(capacity=2000)
        self.ab_test_manager = ABTestManager()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # 学习策略
        self.learning_strategies: Dict[str, Dict[str, Any]] = {}
        
        logger.info("自适应学习引擎初始化完成")
    
    def record_execution(self, agent_type: str, task_params: Dict[str, Any], 
                        result: Dict[str, Any], duration: float):
        """记录执行经验"""
        experience = {
            "agent_type": agent_type,
            "task_params": task_params,
            "success": result.get("status") == "success",
            "result": result,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        self.experience_buffer.add_experience(experience)
        
        # 记录性能指标
        self.performance_analyzer.record_metric(
            agent_type, 
            "duration", 
            duration,
            {"task_type": task_params.get("task_type", "unknown")}
        )
        
        self.performance_analyzer.record_metric(
            agent_type,
            "success_rate",
            1.0 if experience["success"] else 0.0
        )
    
    def get_learning_insights(self, agent_type: str) -> Dict[str, Any]:
        """获取学习洞察"""
        insights = {
            "agent_type": agent_type,
            "experience_count": len(self.experience_buffer.get_experiences_by_agent(agent_type)),
            "overall_success_rate": self.experience_buffer.get_success_rate(agent_type),
            "performance_report": self.performance_analyzer.get_performance_report(agent_type),
            "optimization_suggestions": self.performance_analyzer.get_optimization_suggestions(agent_type),
            "recent_trends": self._analyze_trends(agent_type)
        }
        
        return insights
    
    def _analyze_trends(self, agent_type: str) -> Dict[str, Any]:
        """分析近期趋势"""
        experiences = self.experience_buffer.get_experiences_by_agent(agent_type)
        
        if len(experiences) < 10:
            return {"message": "数据不足，无法分析趋势"}
        
        # 分析最近10次和之前10次的成功率对比
        recent = experiences[-10:]
        older = experiences[-20:-10] if len(experiences) >= 20 else experiences[:10]
        
        recent_success = sum(1 for exp in recent if exp.get("success")) / len(recent)
        older_success = sum(1 for exp in older if exp.get("success")) / len(older)
        
        trend = "improving" if recent_success > older_success else "declining" if recent_success < older_success else "stable"
        
        return {
            "trend": trend,
            "recent_success_rate": recent_success,
            "previous_success_rate": older_success,
            "change": recent_success - older_success
        }
    
    def recommend_strategy(self, agent_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """推荐最优策略"""
        insights = self.get_learning_insights(agent_type)
        
        # 基于历史经验推荐
        experiences = self.experience_buffer.get_experiences_by_agent(agent_type)
        
        if not experiences:
            return {
                "recommendation": "暂无历史数据，使用默认策略",
                "confidence": 0.0
            }
        
        # 找出最成功的任务参数组合
        successful_exps = [exp for exp in experiences if exp.get("success")]
        
        if not successful_exps:
            return {
                "recommendation": "历史成功率较低，建议调整任务参数",
                "confidence": 0.0
            }
        
        # 简单的模式识别（可以扩展为更复杂的ML算法）
        common_patterns = defaultdict(int)
        for exp in successful_exps:
            task_type = exp.get("task_params", {}).get("task_type", "unknown")
            common_patterns[task_type] += 1
        
        best_pattern = max(common_patterns.keys(), key=lambda k: common_patterns[k])
        confidence = common_patterns[best_pattern] / len(successful_exps)
        
        return {
            "recommendation": f"推荐使用任务类型: {best_pattern}",
            "best_task_type": best_pattern,
            "confidence": confidence,
            "supporting_evidence": f"在 {len(successful_exps)} 次成功执行中，{common_patterns[best_pattern]} 次使用了该类型"
        }


# 全局学习引擎实例
adaptive_learning_engine = AdaptiveLearningEngine()
