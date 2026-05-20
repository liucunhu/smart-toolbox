"""
今日头条自动化任务
包含：自动发布文章、数据抓取、账号健康检查、收益统计、热点监控等
"""
import asyncio
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import Account, PlatformEnum
from app.utils.logger import logger


@celery_app.task(bind=True, max_retries=3)
def auto_publish_toutiao_task(self, article_id: int):
    """
    自动发布头条文章任务（支持定时发布）
    
    :param article_id: 文章ID
    """
    db = SessionLocal()
    try:
        from app.models import Article
        from app.services.publish.toutiao_publisher import ToutiaoPublisher
        
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            logger.error(f"文章 {article_id} 不存在")
            return {"status": "error", "error": "文章不存在"}
        
        # 检查是否为定时发布
        if article.scheduled_publish_time and article.scheduled_publish_time > datetime.now():
            logger.info(f"文章 {article_id} 未到发布时间， scheduled: {article.scheduled_publish_time}")
            return {"status": "scheduled", "scheduled_time": article.scheduled_publish_time}
        
        account = db.query(Account).filter(Account.id == article.account_id).first()
        if not account:
            logger.error(f"账号 {article.account_id} 不存在")
            return {"status": "error", "error": "账号不存在"}
        
        # 更新状态为处理中
        article.status = "processing"
        db.commit()
        
        # 执行发布
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        publisher = ToutiaoPublisher(account_id=account.id)
        
        try:
            result = loop.run_until_complete(
                publisher.initialize_with_cdp(cdp_port=9222)
            )
            
            # 使用Cookie登录
            if account.cookies:
                login_result = loop.run_until_complete(
                    publisher.smart_login(cookies=account.cookies)
                )
                
                if not login_result:
                    raise Exception("登录失败")
            
            # 发布文章
            publish_result = loop.run_until_complete(
                publisher.publish_article(
                    title=article.title,
                    content=article.content,
                    category=article.category or "科技",
                    tags=article.tags or [],
                    cover_image_path=article.cover_image_path,
                    account_id=account.id
                )
            )
            
            if publish_result["status"] == "success":
                article.status = "published"
                article.published_time = datetime.now()
                article.platform_article_id = publish_result.get("article_id")
                db.commit()
                
                logger.info(f"✅ 文章 {article_id} 发布成功")
                return {"status": "success", "article_id": article_id}
            else:
                raise Exception(publish_result.get("error", "发布失败"))
        
        except Exception as e:
            logger.error(f"发布失败: {e}")
            article.status = "failed"
            db.commit()
            
            # 重试逻辑
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
            
            return {"status": "error", "error": str(e)}
        
        finally:
            loop.run_until_complete(publisher.close())
            loop.close()
        
    except Exception as e:
        logger.error(f"自动发布任务失败: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def fetch_toutiao_analytics_task(self, account_id: int, days: int = 7):
    """
    抓取头条账号数据分析
    
    :param account_id: 账号ID
    :param days: 抓取天数
    """
    db = SessionLocal()
    try:
        from app.services.analytics.toutiao_analytics import ToutiaoAnalyticsService
        
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            logger.error(f"账号 {account_id} 不存在")
            return {"status": "error", "error": "账号不存在"}
        
        logger.info(f"开始抓取账号 {account_id} 的数据分析（{days}天）")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        service = ToutiaoAnalyticsService(account_id=account_id, db=db)
        
        try:
            loop.run_until_complete(service.initialize(use_cdp=True, cdp_port=9222))
            
            # 登录
            login_success = loop.run_until_complete(service.login_if_needed(use_cdp=True))
            if not login_success:
                raise Exception("登录失败")
            
            # 抓取数据
            analytics_data = loop.run_until_complete(service.fetch_articles_data(days=days))
            
            if analytics_data:
                logger.info(f"✅ 成功抓取 {len(analytics_data)} 篇文章的数据")
                
                # 更新账号统计数据
                total_views = sum(item.get("views", 0) for item in analytics_data)
                total_likes = sum(item.get("likes", 0) for item in analytics_data)
                total_comments = sum(item.get("comments", 0) for item in analytics_data)
                
                account.daily_income = total_views * 0.008  # 估算收益
                account.monthly_income = account.daily_income * 30
                
                db.commit()
                
                return {
                    "status": "success",
                    "articles_count": len(analytics_data),
                    "total_views": total_views,
                    "total_likes": total_likes,
                    "total_comments": total_comments
                }
            else:
                raise Exception("数据抓取失败")
        
        finally:
            loop.run_until_complete(service.close())
            loop.close()
        
    except Exception as e:
        logger.error(f"数据抓取失败: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120)
        
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def check_account_health_task():
    """
    检查所有头条账号的健康状态
    """
    db = SessionLocal()
    try:
        from app.services.operations.health_monitor import AccountHealthService
        from app.models import Article
        
        logger.info("开始检查头条账号健康状态")
        
        accounts = db.query(Account).filter(
            Account.platform == PlatformEnum.TOUTIAO
        ).all()
        
        health_service = AccountHealthService(db)
        warning_accounts = []
        
        for account in accounts:
            # 获取最近7天的文章数据
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            recent_articles = db.query(Article).filter(
                Article.account_id == account.id,
                Article.published_time >= seven_days_ago,
                Article.status == "published"
            ).all()
            
            # 计算健康指标
            if recent_articles:
                total_views = sum(a.views or 0 for a in recent_articles)
                total_likes = sum(a.likes or 0 for a in recent_articles)
                total_comments = sum(a.comments or 0 for a in recent_articles)
                
                avg_views = total_views / len(recent_articles)
                interaction_rate = (total_likes + total_comments) / max(total_views, 1)
                
                # 更新健康分
                metrics = {
                    "views": avg_views,
                    "interaction_rate": interaction_rate
                }
                
                health_score = health_service.update_health_score(account.id, metrics)
                
                # 检测异常
                if health_score < 60:
                    warning_accounts.append({
                        "account_id": account.id,
                        "account_name": account.username,
                        "health_score": health_score,
                        "severity": "critical" if health_score < 40 else "warning",
                        "message": f"账号健康度低（{health_score:.1f}分）"
                    })
                    
                    logger.warning(f"⚠️  账号 {account.username} 健康度低: {health_score:.1f}")
            else:
                # 无近期文章，检查最后发布时间
                last_article = db.query(Article).filter(
                    Article.account_id == account.id,
                    Article.status == "published"
                ).order_by(Article.published_time.desc()).first()
                
                if last_article and last_article.published_time:
                    days_since_update = (datetime.now() - last_article.published_time).days
                    
                    if days_since_update >= 3:
                        warning_accounts.append({
                            "account_id": account.id,
                            "account_name": account.username,
                            "health_score": 50,
                            "severity": "warning",
                            "message": f"已{days_since_update}天未更新"
                        })
                        
                        logger.warning(f"⚠️  账号 {account.username} 已{days_since_update}天未更新")
        
        # 发送预警通知
        if warning_accounts:
            logger.warning(f"发现 {len(warning_accounts)} 个账号健康预警")
            
            try:
                from app.services.operations.alert_system import AlertSystem
                alert_system = AlertSystem()
                
                for warning in warning_accounts:
                    message = (
                        f"⚠️ 账号健康预警\n"
                        f"账号：{warning['account_name']}\n"
                        f"健康度：{warning['health_score']:.1f}分\n"
                        f"问题：{warning['message']}\n\n"
                        f"建议操作：\n"
                        f"1. 检查近期内容质量\n"
                        f"2. 增加互动引导\n"
                        f"3. 避免敏感话题"
                    )
                    
                    subject = f"账号健康预警：{warning['account_name']}"
                    
                    import asyncio
                    tasks = []
                    
                    tasks.append(
                        alert_system.send_email_alert(subject=subject, message=message)
                    )
                    
                    tasks.append(
                        alert_system.send_dingtalk_alert(message)
                    )
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                    loop.close()
                    
                    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
                    
                    if success_count > 0:
                        logger.info(f"✅ 已发送健康预警通知 ({success_count}/{len(tasks)}渠道): {warning['account_name']}")
                        
            except Exception as e:
                logger.error(f"发送通知失败: {e}")
        
        logger.info("✅ 账号健康检查完成")
        return {
            "status": "success",
            "warning_count": len(warning_accounts),
            "warnings": warning_accounts
        }
        
    except Exception as e:
        logger.error(f"账号健康检查失败: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def update_income_stats_task():
    """
    更新所有头条账号的收益统计
    """
    db = SessionLocal()
    try:
        from app.models import Article
        
        logger.info("开始更新头条账号收益统计")
        
        accounts = db.query(Account).filter(
            Account.platform == PlatformEnum.TOUTIAO
        ).all()
        
        for account in accounts:
            # 查询最近7天的文章数据
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            articles = db.query(Article).filter(
                Article.account_id == account.id,
                Article.published_time >= seven_days_ago,
                Article.status == "published"
            ).all()
            
            # 计算收益
            total_views = sum(a.views or 0 for a in articles)
            daily_income = total_views * 0.008  # 假设CPM为8元
            monthly_income = daily_income * 30
            
            # 累计总收益
            all_articles = db.query(Article).filter(
                Article.account_id == account.id,
                Article.status == "published"
            ).all()
            
            total_all_views = sum(a.views or 0 for a in all_articles)
            total_income = total_all_views * 0.008
            
            # 更新账号收益字段
            account.daily_income = daily_income
            account.monthly_income = monthly_income
            account.total_income = total_income
            
            logger.info(
                f"账号 {account.username}: 日收益={daily_income:.2f}, "
                f"月收益={monthly_income:.2f}, 总收益={total_income:.2f}"
            )
        
        db.commit()
        logger.info("✅ 收益统计更新完成")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"收益统计更新失败: {e}")
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def hot_topic_monitor_task():
    """
    监控热点话题并自动生成选题建议
    """
    db = SessionLocal()
    try:
        from app.services.content.hot_trend_injector import HotTrendInjector
        
        logger.info("开始监控热点话题")
        
        injector = HotTrendInjector()
        
        # 获取头条热点
        hot_topics = injector.fetch_hot_topics(platform="toutiao", count=20)
        
        if hot_topics:
            logger.info(f"✅ 获取到 {len(hot_topics)} 个热点话题")
            
            # 可以保存到数据库或缓存
            # TODO: 实现热点话题存储和推荐逻辑
            
            return {
                "status": "success",
                "topics_count": len(hot_topics),
                "topics": hot_topics[:10]  # 返回前10个
            }
        else:
            logger.warning("未获取到热点话题")
            return {"status": "success", "topics_count": 0}
        
    except Exception as e:
        logger.error(f"热点监控失败: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
