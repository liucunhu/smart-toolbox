"""
文章数据分析API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.analytics.toutiao_analytics import get_analytics_service
from app.models import Account
from app.utils.logger import logger

router = APIRouter(prefix="/analytics", tags=["数据分析"])

@router.get("/articles/{account_id}", summary="获取账号的文章数据分析")
async def get_article_analytics(
    account_id: int,
    db: Session = Depends(get_db)
):
    """获取指定账号的文章数据分析
    
    使用CDP连接Edge浏览器（如果可用），否则使用Cookie登录
    """
    try:
        # 验证账号是否存在
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="账号不存在")
        
        logger.info(f"📊 开始获取账号 {account_id} 的文章数据分析...")
        
        # 获取数据分析服务
        service = get_analytics_service(account_id=account_id, db=db)
        
        # 初始化浏览器（优先使用CDP）
        await service.initialize(use_cdp=True, cdp_port=9222)
        
        try:
            # 登录检查（优先使用数据库中的Cookie，CDP连接则直接使用Edge的登录状态）
            login_success = await service.login_if_needed(use_cdp=True)
            if not login_success:
                raise HTTPException(
                    status_code=401,
                    detail="登录失败：Cookie不存在或已过期，请先在账号管理中登录该头条账号"
                )
            
            # 获取文章数据
            articles_data = await service.fetch_article_analytics(use_cdp=True)
            
            # 计算统计数据
            total_articles = len(articles_data)
            total_shows = sum(article.get('show_count', 0) for article in articles_data)
            total_reads = sum(article.get('read_count', 0) for article in articles_data)
            total_likes = sum(article.get('like_count', 0) for article in articles_data)
            total_comments = sum(article.get('comment_count', 0) for article in articles_data)
            
            # === 智能分析引擎 ===
            suggestions = []
            optimized_prompt_template = ""
            content_strategy = {}
            
            if total_articles > 0:
                # 1. 基础指标分析
                avg_read_rate = (total_reads / total_shows * 100) if total_shows > 0 else 0
                avg_interaction_rate = ((total_likes + total_comments) / total_reads * 100) if total_reads > 0 else 0
                avg_likes_per_article = total_likes / total_articles if total_articles > 0 else 0
                avg_comments_per_article = total_comments / total_articles if total_articles > 0 else 0
                
                # 2. 阅读率深度分析
                if avg_read_rate < 3:
                    suggestions.append("🔴 阅读率极低（{:.1f}%），标题吸引力严重不足".format(avg_read_rate))
                    suggestions.append("   → 建议：使用悬念式标题、数字量化、痛点直击")
                elif avg_read_rate < 5:
                    suggestions.append("🟡 阅读率偏低（{:.1f}%），需要优化标题关键词".format(avg_read_rate))
                    suggestions.append("   → 建议：增加热点词汇、行业术语、时效性表达")
                elif avg_read_rate >= 10:
                    suggestions.append("🟢 阅读率优秀（{:.1f}%），标题策略有效".format(avg_read_rate))
                
                # 3. 互动率深度分析
                if avg_interaction_rate < 1:
                    suggestions.append("🔴 互动率极低（{:.1f}%），内容缺乏共鸣".format(avg_interaction_rate))
                    suggestions.append("   → 建议：增加情感化表达、设置互动话题、引导评论")
                elif avg_interaction_rate < 3:
                    suggestions.append("🟡 互动率一般（{:.1f}%），可进一步提升".format(avg_interaction_rate))
                    suggestions.append("   → 建议：文末添加投票、提问、征集观点")
                elif avg_interaction_rate >= 5:
                    suggestions.append("🟢 互动率优秀（{:.1f}%），用户参与度高".format(avg_interaction_rate))
                
                # 4. 文章表现差异分析
                if len(articles_data) >= 2:
                    sorted_by_reads = sorted(articles_data, key=lambda x: x.get('read_count', 0), reverse=True)
                    sorted_by_interactions = sorted(articles_data, key=lambda x: x.get('like_count', 0) + x.get('comment_count', 0), reverse=True)
                    
                    best_by_reads = sorted_by_reads[0]
                    worst_by_reads = sorted_by_reads[-1]
                    best_by_interactions = sorted_by_interactions[0]
                    
                    # 找出高流量文章的特征
                    read_variance = best_by_reads.get('read_count', 0) / (worst_by_reads.get('read_count', 1) if worst_by_reads.get('read_count', 0) > 0 else 1)
                    
                    if read_variance > 5:
                        suggestions.append(f"\n📊 表现差异显著（最高/最低 = {read_variance:.1f}倍）")
                        suggestions.append(f"   🏆 最佳文章：{best_by_reads['title'][:40]}...")
                        suggestions.append(f"      - 展现: {best_by_reads.get('show_count', 0):,}")
                        suggestions.append(f"      - 阅读: {best_by_reads.get('read_count', 0):,}")
                        suggestions.append(f"      - 点赞: {best_by_reads.get('like_count', 0):,}")
                        suggestions.append(f"      - 评论: {best_by_reads.get('comment_count', 0):,}")
                        
                        # 5. 生成优化后的提示词模板
                        optimized_prompt_template = f"""【基于数据分析的优化提示词】

🎯 目标受众分析：
- 根据历史数据，您的受众偏好：高互动、实用性强的内容
- 建议主题方向：解决实际问题、提供具体方法、案例佐证

📝 标题优化策略：
- 格式：[数字] + [痛点/需求] + [解决方案/效果]
- 示例："3个技巧让你XXX"、"为什么XXX总是失败？这5点很关键"
- 关键词：加入行业热词、时效性词汇（最新、2024、趋势）

📖 内容结构建议：
1. 开头（100-150字）：痛点引入 + 数据支撑 + 承诺价值
2. 主体（分3-5个小节）：
   - 每节500-800字
   - 每节一个小标题（问题式或数字式）
   - 包含具体案例、数据、实操步骤
3. 结尾（100-150字）：总结要点 + 行动号召 + 互动引导

💬 互动优化：
- 文中设置2-3个思考问题
- 文末添加投票或征集观点
- 鼓励读者分享自己的经验

🎨 视觉优化：
- 每300-500字插入一张配图
- 使用列表、表格、引用框增强可读性
- 重点内容加粗或标红

⚡ 发布时机：
- 最佳发布时间：工作日早8-9点、晚7-9点
- 避免周末和节假日发布
"""
                        
                        content_strategy = {
                            "high_performing_topics": ["实用性教程", "案例分析", "数据驱动"],
                            "recommended_title_formats": [
                                "数字+痛点+方案",
                                "疑问句+揭秘",
                                "对比式+结果"
                            ],
                            "optimal_content_length": "1500-2500字",
                            "interaction_boosters": ["投票", "问答", "经验分享"]
                        }
                    
                    # 6. 如果互动最好的文章和阅读最好的不同，给出特别建议
                    if best_by_interactions['title'] != best_by_reads['title']:
                        suggestions.append(f"\n💡 发现：互动最高的文章与阅读最高的不同")
                        suggestions.append(f"   互动冠军：{best_by_interactions['title'][:40]}...")
                        suggestions.append(f"   → 这类内容更能引发讨论，可增加此类选题")
                
                # 7. 通用优化建议
                if not optimized_prompt_template:
                    optimized_prompt_template = f"""【文章生成优化提示词】

📌 核心原则：
- 内容为王：提供真实价值，避免空洞说教
- 用户视角：从读者痛点出发，而非自嗨
- 数据支撑：用具体数字、案例增强说服力

🎯 标题公式：
- [数字]个[方法/技巧]帮你[解决什么问题]
- 为什么[常见现象]？[数字]个原因告诉你真相
- [权威背书]+[核心价值]+[紧迫感]

📖 内容框架：
1. 痛点场景描述（引起共鸣）
2. 问题分析（展示专业度）
3. 解决方案（具体可操作）
4. 案例证明（增强可信度）
5. 行动指南（降低执行门槛）

💬 提升互动：
- 设置开放性问题
- 邀请读者分享经验
- 提供额外资源（模板、工具、清单）
"""
            
            return {
                "status": "success",
                "total": total_articles,
                "summary": {
                    "total_articles": total_articles,
                    "total_shows": total_shows,
                    "total_reads": total_reads,
                    "total_likes": total_likes,
                    "total_comments": total_comments,
                    "avg_read_rate": round(avg_read_rate, 2) if total_articles > 0 else 0,
                    "avg_interaction_rate": round(avg_interaction_rate, 2) if total_articles > 0 else 0,
                    "avg_likes_per_article": round(avg_likes_per_article, 2),
                    "avg_comments_per_article": round(avg_comments_per_article, 2)
                },
                "articles": articles_data,
                "analysis": {
                    "suggestions": suggestions,
                    "optimized_prompt_template": optimized_prompt_template,
                    "content_strategy": content_strategy if content_strategy else None,
                    "performance_insights": {
                        "read_rate_level": "优秀" if avg_read_rate >= 10 else "良好" if avg_read_rate >= 5 else "需优化" if avg_read_rate >= 3 else "较差",
                        "interaction_level": "优秀" if avg_interaction_rate >= 5 else "良好" if avg_interaction_rate >= 3 else "需优化" if avg_interaction_rate >= 1 else "较差",
                        "content_consistency": "稳定" if total_articles >= 5 and read_variance < 3 else "波动较大" if total_articles >= 2 else "数据不足"
                    }
                }
            }
            
            # === 保存分析结果到缓存（用于后续文章生成）===
            try:
                from app.services.analytics.analytics_cache import get_analytics_cache_service
                cache_service = get_analytics_cache_service(db)
                cache_service.save_analysis_result(account_id, {
                    "suggestions": suggestions,
                    "optimized_prompt_template": optimized_prompt_template,
                    "content_strategy": content_strategy,
                    "performance_insights": {
                        "read_rate_level": "优秀" if avg_read_rate >= 10 else "良好" if avg_read_rate >= 5 else "需优化" if avg_read_rate >= 3 else "较差",
                        "interaction_level": "优秀" if avg_interaction_rate >= 5 else "良好" if avg_interaction_rate >= 3 else "需优化" if avg_interaction_rate >= 1 else "较差",
                        "content_consistency": "稳定" if total_articles >= 5 and read_variance < 3 else "波动较大" if total_articles >= 2 else "数据不足"
                    }
                }, ttl_hours=24)
                logger.info(f"✅ 分析结果已缓存，将在下次发布时自动应用")
            except Exception as e:
                logger.warning(f"⚠️  缓存分析结果失败: {e}")
            
        finally:
            # 关闭浏览器
            await service.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取文章数据分析失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取文章数据分析失败: {str(e)}")


@router.post("/evolve/{account_id}", summary="触发自适应内容进化")
async def trigger_content_evolution(
    account_id: int,
    days: int = 5,
    db: Session = Depends(get_db)
):
    """
    触发自适应内容进化分析
    
    基于历史数据（前N天）深度分析，自动优化：
    - 标题模式学习
    - 内容结构优化
    - 封面提示词进化
    - 发布时间优化
    
    Args:
        account_id: 账号ID
        days: 分析天数（默认5天）
    
    Returns:
        进化建议和优化策略
    """
    try:
        # 验证账号是否存在
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="账号不存在")
        
        logger.info(f"🧬 开始触发自适应内容进化（账号{account_id}，近{days}天）")
        
        # 调用自适应进化引擎
        from app.services.analytics.adaptive_content_evolver import evolve_content_strategy
        
        evolution_result = await evolve_content_strategy(
            account_id=account_id,
            db=db,
            days=days
        )
        
        if evolution_result.get("status") == "success":
            logger.info(f"✅ 自适应进化完成")
            logger.info(f"   数据点: {evolution_result['data_points']}")
            logger.info(f"   标题模式: {evolution_result.get('title_patterns', {}).get('most_successful', 'N/A')}")
            logger.info(f"   封面优化: {len(evolution_result.get('cover_optimization', {}).get('style_recommendations', {}))}个分类")
            
            return {
                "status": "success",
                "message": "自适应进化分析完成，优化策略已应用到账号配置",
                "data": evolution_result
            }
        elif evolution_result.get("status") == "insufficient_data":
            logger.warning(f"⚠️  数据不足，无法进行进化分析")
            return {
                "status": "warning",
                "message": evolution_result.get("message", "数据点不足"),
                "current_count": evolution_result.get("current_count", 0),
                "required_count": 10
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=evolution_result.get("error", "进化分析失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 自适应进化失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"自适应进化失败: {str(e)}")
