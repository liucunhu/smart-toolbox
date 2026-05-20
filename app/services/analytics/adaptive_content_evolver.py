"""
自适应内容进化引擎
基于历史数据分析，自动优化文章生成和封面生成策略
支持：标题模式学习、内容结构优化、封面提示词进化
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.utils.logger import logger


class AdaptiveContentEvolver:
    """自适应内容进化引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # 进化策略配置
        self.evolution_config = {
            "analysis_window_days": 5,  # 分析窗口：前5天
            "min_data_points": 10,      # 最少数据点数量
            "success_threshold": 0.7,   # 成功阈值（阅读率前70%）
            "evolution_rate": 0.3       # 进化速率（30%新策略 + 70%旧策略）
        }
        
        # 封面风格库
        self.cover_style_patterns = {
            "modern": {
                "keywords": ["现代", "科技感", "未来感", "简约"],
                "colors": ["蓝色", "紫色", "渐变"],
                "composition": "居中构图"
            },
            "bold": {
                "keywords": ["大胆", "鲜艳", "对比强烈", "视觉冲击"],
                "colors": ["红色", "橙色", "黄色"],
                "composition": "三分法构图"
            },
            "minimal": {
                "keywords": ["极简", "留白", "清新", "干净"],
                "colors": ["白色", "浅色", "单色"],
                "composition": "极简构图"
            }
        }
    
    async def analyze_and_evolve(
        self,
        account_id: int,
        days: int = None
    ) -> Dict:
        """
        执行完整的分析和进化流程
        
        Args:
            account_id: 账号ID
            days: 分析天数（默认使用配置值）
            
        Returns:
            {
                "status": "success",
                "analysis_period": "2026-05-07 to 2026-05-12",
                "data_points": 25,
                "title_patterns": {...},
                "content_structure": {...},
                "cover_optimization": {...},
                "evolution_suggestions": {...}
            }
        """
        if days is None:
            days = self.evolution_config["analysis_window_days"]
        
        logger.info(f"🧬 开始自适应内容进化分析（账号{account_id}，近{days}天）")
        
        try:
            # 步骤1: 拉取历史数据
            historical_data = await self._fetch_historical_data(account_id, days)
            
            if not historical_data or len(historical_data) < self.evolution_config["min_data_points"]:
                logger.warning(f"⚠️  数据点不足（{len(historical_data) if historical_data else 0}个），需要至少{self.evolution_config['min_data_points']}个")
                return {
                    "status": "insufficient_data",
                    "message": f"数据点不足，需要至少{self.evolution_config['min_data_points']}篇文章",
                    "current_count": len(historical_data) if historical_data else 0
                }
            
            logger.info(f"✅ 获取到 {len(historical_data)} 条历史数据")
            
            # 步骤2: 深度分析
            analysis_result = self._deep_analyze(historical_data)
            logger.info(f"✅ 深度分析完成")
            
            # 步骤3: 识别成功模式
            success_patterns = self._identify_success_patterns(historical_data, analysis_result)
            logger.info(f"✅ 识别到 {len(success_patterns)} 个成功模式")
            
            # 步骤4: 生成进化建议
            evolution_suggestions = self._generate_evolution_suggestions(
                analysis_result, 
                success_patterns
            )
            logger.info(f"✅ 生成进化建议")
            
            # 步骤5: 保存进化结果到数据库
            await self._save_evolution_result(account_id, evolution_suggestions)
            
            logger.info(f"🎉 自适应进化分析完成")
            logger.info(f"   分析周期: {analysis_result['period']}")
            logger.info(f"   数据点: {len(historical_data)}")
            logger.info(f"   成功模式: {len(success_patterns)}个")
            
            return {
                "status": "success",
                "analysis_period": analysis_result["period"],
                "data_points": len(historical_data),
                "title_patterns": success_patterns.get("title_patterns", {}),
                "content_structure": success_patterns.get("content_structure", {}),
                "cover_optimization": evolution_suggestions.get("cover_optimization", {}),
                "evolution_suggestions": evolution_suggestions
            }
            
        except Exception as e:
            logger.error(f"❌ 自适应进化分析失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _fetch_historical_data(self, account_id: int, days: int) -> List[Dict]:
        """
        拉取历史文章数据
        
        Returns:
            包含文章信息和表现指标的列表
        """
        from app.models import Account, PublishRecord, ContentTask
        
        try:
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"📊 查询时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
            
            # 查询该账号在指定时间范围内的发布记录
            records = self.db.query(PublishRecord).join(
                ContentTask, 
                PublishRecord.content_task_id == ContentTask.id
            ).filter(
                PublishRecord.account_id == account_id,
                PublishRecord.publish_time >= start_date,
                PublishRecord.publish_time <= end_date,
                PublishRecord.publish_status == "published"
            ).order_by(
                PublishRecord.publish_time.desc()
            ).all()
            
            historical_data = []
            
            for record in records:
                task = record.content_task
                
                # 尝试从头条API获取详细数据（阅读量、点赞等）
                metrics = await self._fetch_article_metrics(record)
                
                data_point = {
                    "id": record.id,
                    "publish_time": record.publish_time,
                    "title": task.article_title if task else "",
                    "content": task.article_content if task else "",
                    "category": task.article_category if task else "",
                    "tags": task.tags if task else [],
                    "metrics": metrics,
                    "read_count": metrics.get("read_count", 0),
                    "like_count": metrics.get("like_count", 0),
                    "comment_count": metrics.get("comment_count", 0),
                    "share_count": metrics.get("share_count", 0)
                }
                
                historical_data.append(data_point)
            
            logger.info(f"✅ 成功获取 {len(historical_data)} 条历史数据")
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ 获取历史数据失败: {e}")
            return []
    
    async def _fetch_article_metrics(self, publish_record) -> Dict:
        """
        获取文章的详细表现指标
        
        优先从缓存获取，如果没有则调用头条API
        """
        try:
            # 尝试从分析缓存获取
            from app.services.analytics.analytics_cache import get_analytics_cache_service
            
            cache_service = get_analytics_cache_service(self.db)
            cached_data = cache_service.get_article_metrics(publish_record.id)
            
            if cached_data:
                return cached_data
            
            # 如果缓存中没有，返回默认值
            # （实际应用中可以调用头条API获取最新数据）
            return {
                "read_count": 0,
                "like_count": 0,
                "comment_count": 0,
                "share_count": 0,
                "show_count": 0
            }
            
        except Exception as e:
            logger.warning(f"⚠️  获取文章指标失败: {e}")
            return {
                "read_count": 0,
                "like_count": 0,
                "comment_count": 0,
                "share_count": 0,
                "show_count": 0
            }
    
    def _deep_analyze(self, historical_data: List[Dict]) -> Dict:
        """
        深度分析历史数据
        
        Returns:
            {
                "period": "...",
                "total_articles": ...,
                "avg_read_count": ...,
                "avg_like_count": ...,
                "high_performing_articles": [...],
                "low_performing_articles": [...],
                "title_length_stats": {...},
                "content_length_stats": {...},
                "category_performance": {...}
            }
        """
        if not historical_data:
            return {}
        
        # 基础统计
        total_articles = len(historical_data)
        avg_read = sum(d["read_count"] for d in historical_data) / total_articles
        avg_like = sum(d["like_count"] for d in historical_data) / total_articles
        avg_comment = sum(d["comment_count"] for d in historical_data) / total_articles
        
        # 按阅读率排序
        sorted_by_reads = sorted(
            historical_data, 
            key=lambda x: x["read_count"], 
            reverse=True
        )
        
        # 高表现文章（前30%）
        high_performing_count = max(1, int(total_articles * 0.3))
        high_performing = sorted_by_reads[:high_performing_count]
        
        # 低表现文章（后30%）
        low_performing = sorted_by_reads[-high_performing_count:]
        
        # 标题长度分析
        title_lengths = [len(d["title"]) for d in historical_data if d["title"]]
        avg_title_length = sum(title_lengths) / max(len(title_lengths), 1)
        
        # 内容长度分析
        content_lengths = [len(d["content"]) for d in historical_data if d["content"]]
        avg_content_length = sum(content_lengths) / max(len(content_lengths), 1)
        
        # 分类表现分析
        category_performance = {}
        for data in historical_data:
            category = data.get("category", "未分类")
            if category not in category_performance:
                category_performance[category] = {
                    "count": 0,
                    "total_reads": 0,
                    "total_likes": 0
                }
            category_performance[category]["count"] += 1
            category_performance[category]["total_reads"] += data["read_count"]
            category_performance[category]["total_likes"] += data["like_count"]
        
        # 计算每个分类的平均表现
        for category, stats in category_performance.items():
            stats["avg_reads"] = stats["total_reads"] / stats["count"]
            stats["avg_likes"] = stats["total_likes"] / stats["count"]
        
        period_start = min(d["publish_time"] for d in historical_data)
        period_end = max(d["publish_time"] for d in historical_data)
        
        return {
            "period": f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
            "total_articles": total_articles,
            "avg_read_count": round(avg_read, 2),
            "avg_like_count": round(avg_like, 2),
            "avg_comment_count": round(avg_comment, 2),
            "high_performing_articles": high_performing,
            "low_performing_articles": low_performing,
            "title_length_stats": {
                "avg": round(avg_title_length, 2),
                "min": min(title_lengths) if title_lengths else 0,
                "max": max(title_lengths) if title_lengths else 0
            },
            "content_length_stats": {
                "avg": round(avg_content_length, 2),
                "min": min(content_lengths) if content_lengths else 0,
                "max": max(content_lengths) if content_lengths else 0
            },
            "category_performance": category_performance
        }
    
    def _identify_success_patterns(self, historical_data: List[Dict], analysis: Dict) -> Dict:
        """
        识别成功模式
        
        Returns:
            {
                "title_patterns": {...},
                "content_structure": {...},
                "optimal_publishing_times": [...],
                "best_categories": [...]
            }
        """
        high_performing = analysis.get("high_performing_articles", [])
        
        if not high_performing:
            return {}
        
        # === 标题模式分析 ===
        title_patterns = self._analyze_title_patterns(high_performing)
        
        # === 内容结构分析 ===
        content_structure = self._analyze_content_structure(high_performing)
        
        # === 最佳发布时间分析 ===
        optimal_times = self._analyze_publishing_times(high_performing)
        
        # === 最佳分类分析 ===
        best_categories = self._analyze_best_categories(high_performing)
        
        return {
            "title_patterns": title_patterns,
            "content_structure": content_structure,
            "optimal_publishing_times": optimal_times,
            "best_categories": best_categories
        }
    
    def _analyze_title_patterns(self, high_performing: List[Dict]) -> Dict:
        """分析高表现文章的标题模式"""
        import re
        
        patterns = {
            "数字型": 0,
            "疑问型": 0,
            "对比型": 0,
            "痛点型": 0,
            "悬念型": 0
        }
        
        pattern_examples = {
            "数字型": [],
            "疑问型": [],
            "对比型": [],
            "痛点型": [],
            "悬念型": []
        }
        
        for article in high_performing:
            title = article.get("title", "")
            
            # 数字型：包含数字
            if re.search(r'\d+', title):
                patterns["数字型"] += 1
                if len(pattern_examples["数字型"]) < 3:
                    pattern_examples["数字型"].append(title)
            
            # 疑问型：包含疑问词
            if re.search(r'(为什么|如何|怎么|什么|吗|呢)', title):
                patterns["疑问型"] += 1
                if len(pattern_examples["疑问型"]) < 3:
                    pattern_examples["疑问型"].append(title)
            
            # 对比型：包含对比词
            if re.search(r'(VS|对比|区别|差异|更好)', title):
                patterns["对比型"] += 1
                if len(pattern_examples["对比型"]) < 3:
                    pattern_examples["对比型"].append(title)
            
            # 痛点型：包含痛点词
            if re.search(r'(总是|经常|困扰|难题|失败)', title):
                patterns["痛点型"] += 1
                if len(pattern_examples["痛点型"]) < 3:
                    pattern_examples["痛点型"].append(title)
            
            # 悬念型：包含悬念词
            if re.search(r'(揭秘|真相|竟然|没想到)', title):
                patterns["悬念型"] += 1
                if len(pattern_examples["悬念型"]) < 3:
                    pattern_examples["悬念型"].append(title)
        
        # 找出最成功的模式
        most_successful_pattern = max(patterns, key=patterns.get)
        
        return {
            "pattern_distribution": patterns,
            "most_successful": most_successful_pattern,
            "examples": pattern_examples[most_successful_pattern][:3],
            "recommendation": f"建议多使用「{most_successful_pattern}」标题模式"
        }
    
    def _analyze_content_structure(self, high_performing: List[Dict]) -> Dict:
        """分析高表现文章的内容结构"""
        content_lengths = [len(a["content"]) for a in high_performing if a.get("content")]
        
        if not content_lengths:
            return {}
        
        avg_length = sum(content_lengths) / len(content_lengths)
        
        # 段落数分析
        paragraph_counts = []
        for article in high_performing:
            content = article.get("content", "")
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            paragraph_counts.append(len(paragraphs))
        
        avg_paragraphs = sum(paragraph_counts) / max(len(paragraph_counts), 1)
        
        return {
            "optimal_content_length": round(avg_length, 0),
            "optimal_paragraph_count": round(avg_paragraphs, 0),
            "length_range": {
                "min": min(content_lengths),
                "max": max(content_lengths)
            },
            "recommendation": f"建议文章长度控制在{int(avg_length*0.8)}-{int(avg_length*1.2)}字，{int(avg_paragraphs*0.8)}-{int(avg_paragraphs*1.2)}个段落"
        }
    
    def _analyze_publishing_times(self, high_performing: List[Dict]) -> List[Dict]:
        """分析最佳发布时间"""
        from collections import Counter
        
        hour_counter = Counter()
        
        for article in high_performing:
            publish_time = article.get("publish_time")
            if publish_time:
                hour = publish_time.hour
                hour_counter[hour] += 1
        
        # 找出最高频的发布时段
        top_hours = hour_counter.most_common(3)
        
        time_slots = []
        for hour, count in top_hours:
            if 6 <= hour < 12:
                period = "早晨"
            elif 12 <= hour < 14:
                period = "中午"
            elif 14 <= hour < 18:
                period = "下午"
            else:
                period = "晚上"
            
            time_slots.append({
                "hour": hour,
                "period": period,
                "article_count": count,
                "time_label": f"{hour:02d}:00-{hour+1:02d}:00"
            })
        
        return time_slots
    
    def _analyze_best_categories(self, high_performing: List[Dict]) -> List[str]:
        """分析最佳分类"""
        from collections import Counter
        
        category_counter = Counter()
        
        for article in high_performing:
            category = article.get("category", "未分类")
            category_counter[category] += 1
        
        # 返回top 3分类
        return [cat for cat, count in category_counter.most_common(3)]
    
    def _generate_evolution_suggestions(
        self, 
        analysis: Dict, 
        success_patterns: Dict
    ) -> Dict:
        """
        生成进化建议
        
        Returns:
            {
                "title_optimization": {...},
                "content_optimization": {...},
                "cover_optimization": {...},
                "publishing_optimization": {...}
            }
        """
        # 标题优化建议
        title_patterns = success_patterns.get("title_patterns", {})
        title_optimization = {
            "recommended_pattern": title_patterns.get("most_successful", ""),
            "pattern_examples": title_patterns.get("examples", []),
            "optimal_length": analysis.get("title_length_stats", {}).get("avg", 25),
            "prompt_template": self._generate_title_prompt_template(title_patterns)
        }
        
        # 内容优化建议
        content_structure = success_patterns.get("content_structure", {})
        content_optimization = {
            "optimal_length": content_structure.get("optimal_content_length", 2000),
            "optimal_paragraphs": content_structure.get("optimal_paragraph_count", 8),
            "structure_recommendation": content_structure.get("recommendation", "")
        }
        
        # 封面优化建议
        cover_optimization = self._generate_cover_optimization(analysis, success_patterns)
        
        # 发布时间优化
        publishing_optimization = {
            "best_times": success_patterns.get("optimal_publishing_times", []),
            "recommendation": "建议在以上时段发布文章，获得更高曝光"
        }
        
        return {
            "title_optimization": title_optimization,
            "content_optimization": content_optimization,
            "cover_optimization": cover_optimization,
            "publishing_optimization": publishing_optimization
        }
    
    def _generate_title_prompt_template(self, title_patterns: Dict) -> str:
        """生成标题优化提示词模板"""
        most_successful = title_patterns.get("most_successful", "")
        examples = title_patterns.get("examples", [])
        
        template = f"""【基于历史数据的标题优化建议】

🎯 推荐标题模式：{most_successful}

📝 成功案例参考：
"""
        for i, example in enumerate(examples[:3], 1):
            template += f"{i}. {example}\n"
        
        template += f"""
💡 优化要点：
1. 优先使用「{most_successful}」标题模式
2. 标题长度控制在20-30字之间
3. 包含核心关键词
4. 制造悬念或冲突，吸引点击
5. 避免标题党，保持真实性
"""
        
        return template
    
    def _generate_cover_optimization(self, analysis: Dict, success_patterns: Dict) -> Dict:
        """
        生成封面优化建议
        
        基于高表现文章的特征，推荐封面风格
        """
        high_performing = analysis.get("high_performing_articles", [])
        
        # 分析高表现文章的共同特征
        categories = [a.get("category", "") for a in high_performing]
        
        # 根据分类推荐封面风格
        style_recommendations = {}
        
        for category in set(categories):
            if category in ["科技", "AI", "互联网"]:
                style_recommendations[category] = {
                    "style": "modern",
                    "prompt_additions": "科技感强，未来感十足，蓝紫色渐变背景",
                    "color_scheme": "蓝色/紫色渐变",
                    "composition": "主体居中，简洁背景"
                }
            elif category in ["生活", "健康", "美食"]:
                style_recommendations[category] = {
                    "style": "minimal",
                    "prompt_additions": "清新自然，明亮色调，留白充足",
                    "color_scheme": "浅色系，暖色调",
                    "composition": "三分法构图，自然光线"
                }
            elif category in ["财经", "商业", "投资"]:
                style_recommendations[category] = {
                    "style": "bold",
                    "prompt_additions": "专业质感，金色元素，权威感强",
                    "color_scheme": "金色/深蓝色",
                    "composition": "对称构图，稳重布局"
                }
            else:
                style_recommendations[category] = {
                    "style": "modern",
                    "prompt_additions": "现代简约，清晰主题，高对比度",
                    "color_scheme": "根据主题灵活调整",
                    "composition": "黄金分割构图"
                }
        
        # 生成通用封面提示词模板
        universal_prompt_template = """【智能封面图生成提示词模板】

🎨 基础要求：
- 分辨率：1920x1080 (16:9)
- 质量：8K超高清，专业摄影质感
- 风格：{style}
- 色彩：{color_scheme}
- 构图：{composition}

✨ 个性化增强：
{prompt_additions}

📝 主题相关：
- 主标题文字清晰可见（预留文字区域）
- 关键视觉元素突出
- 适合今日头条平台展示
- 高点击率设计

💡 优化建议：
- 避免过多文字遮挡主体
- 保持视觉焦点清晰
- 色彩饱和度适中
- 符合平台审核规范
"""
        
        return {
            "style_recommendations": style_recommendations,
            "universal_prompt_template": universal_prompt_template,
            "evolution_strategy": "根据文章分类自动选择对应的封面风格"
        }
    
    async def _save_evolution_result(self, account_id: int, evolution_suggestions: Dict):
        """保存进化结果到数据库"""
        try:
            from app.models import Account
            
            # 更新账号的进化配置
            account = self.db.query(Account).filter(Account.id == account_id).first()
            
            if account:
                # 将进化建议存储为JSON
                import json
                account.evolution_config = json.dumps(evolution_suggestions, ensure_ascii=False)
                account.last_evolution_time = datetime.now()
                
                self.db.commit()
                logger.info(f"✅ 进化结果已保存到账号 {account_id}")
            else:
                logger.warning(f"⚠️  账号 {account_id} 不存在，无法保存进化结果")
                
        except Exception as e:
            logger.error(f"❌ 保存进化结果失败: {e}")
            self.db.rollback()


# 便捷函数
async def evolve_content_strategy(account_id: int, db: Session, days: int = 5) -> Dict:
    """
    便捷函数：执行内容策略进化
    
    Usage:
        result = await evolve_content_strategy(account_id=1, db=db, days=5)
    """
    evolver = AdaptiveContentEvolver(db)
    return await evolver.analyze_and_evolve(account_id, days)
