"""
智能调度发布服务（增强版）
实现粉丝活跃时段分析和错峰机制
"""
import asyncio
import random
import logging
from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """平台类型"""
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    XIAOHONGSHU = "xiaohongshu"
    TOUTIAO = "toutiao"
    BILIBILI = "bilibili"
    WECHAT = "wechat"


@dataclass
class ActiveTimeSlot:
    """活跃时间段"""
    start_hour: int
    end_hour: int
    weekday_only: bool = False
    weekend_only: bool = False
    base_score: float = 1.0  # 基础活跃度分数
    
    def is_active(self, current_time: datetime) -> bool:
        """检查当前时间是否在活跃时段"""
        hour = current_time.hour
        
        # 检查星期限制
        if self.weekday_only and current_time.weekday() >= 5:
            return False
        if self.weekend_only and current_time.weekday() < 5:
            return False
        
        # 检查小时范围
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour < self.end_hour
        else:
            # 跨天的情况（如 22:00 - 02:00）
            return hour >= self.start_hour or hour < self.end_hour


class FanActivityAnalyzer:
    """粉丝活跃度分析器"""
    
    # 各平台用户的活跃时段（基于行业数据）
    PLATFORM_ACTIVE_SLOTS = {
        PlatformType.DOUYIN: [
            ActiveTimeSlot(7, 9, base_score=0.7),      # 早上通勤
            ActiveTimeSlot(12, 14, base_score=0.8),    # 午休
            ActiveTimeSlot(18, 20, base_score=0.9),    # 晚饭前
            ActiveTimeSlot(20, 23, base_score=1.0),    # 晚间黄金时段
            ActiveTimeSlot(23, 1, base_score=0.6),     # 深夜
        ],
        PlatformType.KUAISHOU: [
            ActiveTimeSlot(7, 9, base_score=0.6),
            ActiveTimeSlot(12, 14, base_score=0.7),
            ActiveTimeSlot(18, 20, base_score=0.8),
            ActiveTimeSlot(20, 23, base_score=0.95),
            ActiveTimeSlot(23, 1, base_score=0.5),
        ],
        PlatformType.XIAOHONGSHU: [
            ActiveTimeSlot(8, 10, base_score=0.8),     # 早上
            ActiveTimeSlot(12, 14, base_score=0.9),    # 午休
            ActiveTimeSlot(18, 19, base_score=0.7),    # 晚饭前
            ActiveTimeSlot(20, 22, base_score=1.0),    # 晚间
            ActiveTimeSlot(22, 24, base_score=0.8),    # 深夜
        ],
        PlatformType.TOUTIAO: [
            ActiveTimeSlot(7, 9, base_score=0.7),
            ActiveTimeSlot(12, 14, base_score=0.9),    # 午休是头条高峰
            ActiveTimeSlot(18, 20, base_score=0.8),
            ActiveTimeSlot(20, 22, base_score=0.95),
            ActiveTimeSlot(22, 0, base_score=0.6),
        ],
        PlatformType.BILIBILI: [
            ActiveTimeSlot(12, 14, base_score=0.7),
            ActiveTimeSlot(17, 19, base_score=0.8),    # 晚饭高峰
            ActiveTimeSlot(19, 22, base_score=1.0),    # B站晚间黄金时段
            ActiveTimeSlot(22, 2, base_score=0.9),     # 深夜活跃（B站特色）
            ActiveTimeSlot(9, 11, base_score=0.6, weekday_only=True),  # 工作日上午
        ],
        PlatformType.WECHAT: [
            ActiveTimeSlot(7, 9, base_score=0.8),      # 早上
            ActiveTimeSlot(12, 14, base_score=0.9),    # 午休
            ActiveTimeSlot(17, 19, base_score=0.7),
            ActiveTimeSlot(20, 22, base_score=1.0),    # 晚间
            ActiveTimeSlot(8, 10, weekend_only=True, base_score=0.9),  # 周末早上
        ],
    }
    
    def __init__(self):
        self.historical_data = defaultdict(list)  # 历史数据
    
    def analyze_activity_score(
        self,
        platform: PlatformType,
        check_time: Optional[datetime] = None
    ) -> float:
        """
        分析指定时间的粉丝活跃度分数
        
        Args:
            platform: 平台类型
            check_time: 检查时间（不指定则使用当前时间）
            
        Returns:
            float: 活跃度分数（0-1）
        """
        if check_time is None:
            check_time = datetime.now()
        
        active_slots = self.PLATFORM_ACTIVE_SLOTS.get(platform, [])
        
        max_score = 0.0
        for slot in active_slots:
            if slot.is_active(check_time):
                max_score = max(max_score, slot.base_score)
        
        # 添加随机波动（模拟真实情况）
        noise = random.uniform(-0.05, 0.05)
        final_score = max(0.0, min(1.0, max_score + noise))
        
        logger.debug(f"{platform.value} @ {check_time.strftime('%H:%M')} 活跃度: {final_score:.2f}")
        return final_score
    
    def get_best_publish_times(
        self,
        platform: PlatformType,
        start_date: datetime,
        days: int = 7
    ) -> List[Tuple[datetime, float]]:
        """
        获取未来指定天数内的最佳发布时间
        
        Args:
            platform: 平台类型
            start_date: 开始日期
            days: 天数
            
        Returns:
            List[Tuple[datetime, float]]: (时间, 活跃度分数) 列表
        """
        best_times = []
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            
            # 每小时检查一次
            for hour in range(24):
                check_time = datetime.combine(current_date, time(hour=hour, minute=0))
                score = self.analyze_activity_score(platform, check_time)
                best_times.append((check_time, score))
        
        # 按分数排序
        best_times.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前N个最佳时间
        top_n = min(10, len(best_times))
        return best_times[:top_n]
    
    def record_publish_result(
        self,
        platform: PlatformType,
        publish_time: datetime,
        views: int,
        likes: int,
        comments: int,
        shares: int
    ):
        """
        记录发布结果用于学习优化
        
        Args:
            platform: 平台
            publish_time: 发布时间
            views: 浏览量
            likes: 点赞数
            comments: 评论数
            shares: 分享数
        """
        # 计算互动率
        if views > 0:
            engagement_rate = (likes + comments + shares) / views
        else:
            engagement_rate = 0.0
        
        # 记录数据
        self.historical_data[platform].append({
            "publish_time": publish_time,
            "hour": publish_time.hour,
            "weekday": publish_time.weekday(),
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "engagement_rate": engagement_rate
        })
        
        logger.info(f"记录发布数据: {platform.value} @ {publish_time}, 互动率: {engagement_rate:.2%}")
    
    def optimize_slots_based_on_history(self, platform: PlatformType):
        """
        基于历史数据优化活跃时段
        
        Args:
            platform: 平台
        """
        platform_data = self.historical_data.get(platform, [])
        
        if len(platform_data) < 10:
            logger.warning(f"{platform.value} 历史数据不足，跳过优化")
            return
        
        # 按小时统计平均互动率
        hour_stats = defaultdict(list)
        for record in platform_data:
            hour_stats[record["hour"]].append(record["engagement_rate"])
        
        # 计算每小时的平均互动率
        hour_avg = {}
        for hour, rates in hour_stats.items():
            if len(rates) > 0:
                hour_avg[hour] = sum(rates) / len(rates)
        
        # 找出表现最好的时段
        if hour_avg:
            best_hours = sorted(hour_avg.items(), key=lambda x: x[1], reverse=True)
            logger.info(f"{platform.value} 历史数据最佳时段: {best_hours[:3]}")
            
            # 更新活跃时段权重（简化处理）
            # 实际应用中应该使用更复杂的机器学习算法
            pass


class StaggeredScheduler:
    """错峰调度器"""
    
    def __init__(self):
        self.publish_history = defaultdict(list)  # IP/账号的发布历史
    
    def calculate_delay(
        self,
        account_id: int,
        platform: PlatformType,
        current_time: Optional[datetime] = None,
        min_delay: int = 60,
        max_delay: int = 900
    ) -> int:
        """
        计算发布延迟（秒）
        
        Args:
            account_id: 账号ID
            platform: 平台
            current_time: 当前时间
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            
        Returns:
            int: 延迟秒数
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 检查该账号最近的发布时间
        key = f"{account_id}_{platform.value}"
        recent_publishes = self.publish_history[key]
        
        # 清理超过24小时的历史记录
        cutoff_time = current_time - timedelta(hours=24)
        self.publish_history[key] = [
            p for p in recent_publishes if p > cutoff_time
        ]
        recent_publishes = self.publish_history[key]
        
        base_delay = random.uniform(min_delay, max_delay)
        
        if not recent_publishes:
            # 没有最近发布记录，使用随机延迟
            delay = int(base_delay)
        else:
            # 有最近发布记录，根据发布频率计算延迟
            last_publish = recent_publishes[-1]
            time_since_last = (current_time - last_publish).total_seconds()
            
            # 如果距离上次发布太近，增加延迟
            if time_since_last < min_delay:
                additional_delay = min_delay - time_since_last
                delay = int(additional_delay + random.uniform(0, 300))
            elif time_since_last < max_delay:
                # 在合理范围内，使用较小随机延迟
                delay = int(random.uniform(60, 300))
            else:
                # 距离上次发布较远，使用标准延迟
                delay = int(base_delay)
        
        logger.debug(f"账号 {account_id} ({platform.value}) 延迟: {delay}秒")
        return delay
    
    def record_publish(self, account_id: int, platform: PlatformType, publish_time: datetime):
        """
        记录发布时间
        
        Args:
            account_id: 账号ID
            platform: 平台
            publish_time: 发布时间
        """
        key = f"{account_id}_{platform.value}"
        self.publish_history[key].append(publish_time)
        
        # 只保留最近24小时的记录
        cutoff_time = publish_time - timedelta(hours=24)
        self.publish_history[key] = [
            p for p in self.publish_history[key] if p > cutoff_time
        ]
    
    def schedule_batch_publish(
        self,
        account_platform_pairs: List[Tuple[int, PlatformType]],
        base_time: Optional[datetime] = None
    ) -> List[Tuple[int, PlatformType, datetime]]:
        """
        批量调度发布（错峰）
        
        Args:
            account_platform_pairs: (账号ID, 平台) 列表
            base_time: 基础时间（不指定则使用当前时间）
            
        Returns:
            List[Tuple[int, PlatformType, datetime]]: (账号ID, 平台, 计划发布时间) 列表
        """
        if base_time is None:
            base_time = datetime.now()
        
        schedule = []
        cumulative_delay = 0
        
        for account_id, platform in account_platform_pairs:
            # 计算延迟
            delay = self.calculate_delay(account_id, platform, base_time)
            cumulative_delay += delay
            
            # 计算计划发布时间
            scheduled_time = base_time + timedelta(seconds=cumulative_delay)
            
            schedule.append((account_id, platform, scheduled_time))
            
            # 记录这次计划
            self.record_publish(account_id, platform, scheduled_time)
        
        logger.info(f"批量调度完成: {len(schedule)} 个任务, 总时长: {cumulative_delay/60:.1f}分钟")
        return schedule
    
    def check_rate_limit(
        self,
        account_id: int,
        platform: PlatformType,
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        检查是否触发频率限制
        
        Args:
            account_id: 账号ID
            platform: 平台
            current_time: 当前时间
            
        Returns:
            Dict: 限制状态
        """
        if current_time is None:
            current_time = datetime.now()
        
        key = f"{account_id}_{platform.value}"
        recent_publishes = self.publish_history[key]
        
        # 清理超过24小时的记录
        cutoff_time = current_time - timedelta(hours=24)
        self.publish_history[key] = [
            p for p in recent_publishes if p > cutoff_time
        ]
        recent_publishes = self.publish_history[key]
        
        # 检查不同时间窗口的发布数量
        one_hour_ago = current_time - timedelta(hours=1)
        one_hour_count = sum(1 for p in recent_publishes if p > one_hour_ago)
        
        six_hours_ago = current_time - timedelta(hours=6)
        six_hours_count = sum(1 for p in recent_publishes if p > six_hours_ago)
        
        one_day_ago = current_time - timedelta(days=1)
        one_day_count = sum(1 for p in recent_publishes if p > one_day_ago)
        
        # 定义限制规则
        limits = {
            "one_hour": {
                "max": 3,  # 每小时最多3条
                "current": one_hour_count,
                "exceeded": one_hour_count >= 3
            },
            "six_hours": {
                "max": 10,  # 每6小时最多10条
                "current": six_hours_count,
                "exceeded": six_hours_count >= 10
            },
            "one_day": {
                "max": 20,  # 每天最多20条
                "current": one_day_count,
                "exceeded": one_day_count >= 20
            }
        }
        
        # 检查是否超过限制
        any_exceeded = any(l["exceeded"] for l in limits.values())
        
        result = {
            "account_id": account_id,
            "platform": platform.value,
            "check_time": current_time.isoformat(),
            "limits": limits,
            "rate_limited": any_exceeded,
            "can_publish": not any_exceeded,
            "suggested_wait_time": self._calculate_wait_time(one_hour_count, one_hour_ago) if any_exceeded else 0
        }
        
        logger.debug(f"频率限制检查: {result}")
        return result
    
    def _calculate_wait_time(self, count: int, last_hour: datetime) -> int:
        """
        计算建议等待时间
        
        Args:
            count: 最近一小时的发布数量
            last_hour: 一小时前的时间
            
        Returns:
            int: 等待时间（秒）
        """
        if count == 0:
            return 0
        
        # 简单策略：如果一小时内发布了N条，建议等待 (N+1)*20分钟
        wait_minutes = (count + 1) * 20
        return wait_minutes * 60


class SmartSchedulerV2:
    """智能调度器（增强版）"""
    
    def __init__(self):
        self.activity_analyzer = FanActivityAnalyzer()
        self.staggered_scheduler = StaggeredScheduler()
    
    def get_optimal_publish_time(
        self,
        account_id: int,
        platform: PlatformType,
        base_time: Optional[datetime] = None,
        consider_stagger: bool = True
    ) -> Dict[str, Any]:
        """
        获取最优发布时间
        
        Args:
            account_id: 账号ID
            platform: 平台
            base_time: 基础时间
            consider_stagger: 是否考虑错峰
            
        Returns:
            Dict: 调度信息
        """
        if base_time is None:
            base_time = datetime.now()
        
        platform_enum = PlatformType(platform) if isinstance(platform, str) else platform
        
        # 获取未来24小时内的最佳时段
        best_times = self.activity_analyzer.get_best_publish_times(
            platform_enum,
            base_time,
            days=1
        )
        
        if not best_times:
            return {
                "success": False,
                "error": "未找到合适的发布时间"
            }
        
        # 选择第一个最佳时段
        optimal_time = best_times[0][0]
        activity_score = best_times[0][1]
        
        # 如果考虑错峰，应用延迟
        if consider_stagger:
            delay = self.staggered_scheduler.calculate_delay(
                account_id,
                platform_enum,
                optimal_time
            )
            optimal_time = optimal_time + timedelta(seconds=delay)
        
        # 检查频率限制
        rate_limit_check = self.staggered_scheduler.check_rate_limit(
            account_id,
            platform_enum,
            base_time
        )
        
        result = {
            "success": True,
            "account_id": account_id,
            "platform": platform_enum.value,
            "suggested_time": optimal_time.isoformat(),
            "activity_score": activity_score,
            "delay_seconds": delay if consider_stagger else 0,
            "rate_limit_check": rate_limit_check,
            "can_publish_now": rate_limit_check["can_publish"],
            "alternatives": [
                {"time": t[0].isoformat(), "score": t[1]}
                for t in best_times[1:5]
            ]  # 提供几个备选时间
        }
        
        logger.info(f"最优发布时间: {result['suggested_time']} (活跃度: {activity_score:.2f})")
        return result
    
    def schedule_multiple_accounts(
        self,
        tasks: List[Dict[str, Any]],
        base_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        多账号批量调度
        
        Args:
            tasks: 任务列表，每个任务包含 account_id, platform, content 等
            base_time: 基础时间
            
        Returns:
            List[Dict]: 调度结果列表
        """
        if base_time is None:
            base_time = datetime.now()
        
        results = []
        
        # 提取账号-平台对
        account_platform_pairs = [
            (t["account_id"], PlatformType(t["platform"]))
            for t in tasks
        ]
        
        # 错峰调度
        staggered_schedule = self.staggered_scheduler.schedule_batch_publish(
            account_platform_pairs,
            base_time
        )
        
        # 为每个任务匹配调度时间
        for i, task in enumerate(tasks):
            account_id, platform, scheduled_time = staggered_schedule[i]
            
            # 检查该时段的活跃度
            platform_enum = PlatformType(task["platform"])
            activity_score = self.activity_analyzer.analyze_activity_score(
                platform_enum,
                scheduled_time
            )
            
            result = {
                "task_id": task.get("task_id", i),
                "account_id": account_id,
                "platform": platform_enum.value,
                "scheduled_time": scheduled_time.isoformat(),
                "activity_score": activity_score,
                "content_summary": task.get("content", "")[:50] + "..." if task.get("content") else ""
            }
            
            results.append(result)
        
        logger.info(f"批量调度完成: {len(results)} 个任务")
        return results
    
    def record_publish_performance(
        self,
        account_id: int,
        platform: PlatformType,
        publish_time: datetime,
        performance_data: Dict[str, int]
    ):
        """
        记录发布表现数据（用于学习优化）
        
        Args:
            account_id: 账号ID
            platform: 平台
            publish_time: 发布时间
            performance_data: 表现数据（views, likes, comments, shares）
        """
        self.activity_analyzer.record_publish_result(
            platform,
            publish_time,
            performance_data.get("views", 0),
            performance_data.get("likes", 0),
            performance_data.get("comments", 0),
            performance_data.get("shares", 0)
        )
        
        # 记录到错峰调度器
        self.staggered_scheduler.record_publish(account_id, platform, publish_time)
        
        logger.info(f"记录表现数据: 账号{account_id}, {platform.value}")


# 创建全局智能调度器实例
_smart_scheduler_v2 = None


def get_smart_scheduler_v2() -> SmartSchedulerV2:
    """
    获取智能调度器实例（单例模式）
    
    Returns:
        SmartSchedulerV2: 智能调度器实例
    """
    global _smart_scheduler_v2
    if _smart_scheduler_v2 is None:
        _smart_scheduler_v2 = SmartSchedulerV2()
    return _smart_scheduler_v2
