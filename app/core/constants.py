"""
矩阵运营相关常量定义
遵循 DRY (Don't Repeat Yourself) 原则
"""

# 账号健康度阈值
HEALTH_SCORE_THRESHOLD_ACTIVE = 80.0
HEALTH_SCORE_THRESHOLD_NURTURING = 60.0

# 养号行为参数
NURTURING_BROWSE_DURATION_MIN = 30  # 最小浏览时长（秒）
NURTURING_BROWSE_DURATION_MAX = 120 # 最大浏览时长（秒）
NURTURING_LIKE_PROBABILITY = 0.3    # 点赞概率

# 发布调度参数
PUBLISH_TIME_WINDOW_START = 8       # 最早发布时间（小时）
PUBLISH_TIME_WINDOW_END = 22        # 最晚发布时间（小时）
MAX_DAILY_PUBLISH_PER_ACCOUNT = 5   # 单账号每日最大发布数

# 平台特定限制
PLATFORM_LIMITS = {
    "douyin": {"max_video_duration": 300, "max_hashtags": 10},
    "xiaohongshu": {"max_video_duration": 600, "max_hashtags": 15},
    "bilibili": {"max_video_duration": 3600, "max_hashtags": 5},
}
