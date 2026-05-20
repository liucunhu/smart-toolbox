"""
番茄小说自动化任务
包含：自动发布章节、数据抓取、断更预警、全勤奖检查等
"""
import asyncio
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import Account, Novel, Chapter, FanqieAnalytics, PlatformEnum
from app.services.publish.fanqie_publisher import FanqiePublisher
from app.utils.logger import logger


@celery_app.task(bind=True, max_retries=3)
def auto_publish_chapter_task(self, chapter_id: int):
    """
    自动发布章节任务（支持定时发布）
    :param chapter_id: 章节ID
    """
    db = SessionLocal()
    try:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"status": "error", "message": "Chapter not found"}
        
        if chapter.status != "scheduled":
            logger.warning(f"章节 {chapter_id} 状态不是 scheduled，跳过")
            return {"status": "skipped", "reason": "not_scheduled"}
        
        # 检查是否到达发布时间
        if chapter.scheduled_time and datetime.now() < chapter.scheduled_time:
            logger.info(f"章节 {chapter_id} 未到发布时间，稍后重试")
            raise self.retry(countdown=300)  # 5分钟后重试
        
        novel = db.query(Novel).filter(Novel.id == chapter.novel_id).first()
        account = db.query(Account).filter(Account.id == novel.account_id).first()
        
        if not novel or not account:
            return {"status": "error", "message": "Novel or Account not found"}
        
        logger.info(f"开始自动发布章节: {chapter.title}")
        
        # 更新状态为处理中
        chapter.status = "processing"
        db.commit()
        
        # 执行发布
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        publisher = FanqiePublisher(account_id=account.id)
        
        try:
            result = loop.run_until_complete(
                publisher.initialize_with_cdp(cdp_port=9222)
            )
            
            # 使用Cookie登录
            if account.writer_cookies:
                login_result = loop.run_until_complete(
                    publisher.login_with_cookies(account.writer_cookies)
                )
                
                if not login_result:
                    raise Exception("登录失败")
            
            # 发布章节
            publish_result = loop.run_until_complete(
                publisher.publish_chapter(
                    novel_id=novel.platform_novel_id or "",
                    chapter_number=chapter.chapter_number,
                    title=chapter.title,
                    content=chapter.content,
                    scheduled_time=None  # 立即发布
                )
            )
            
            if publish_result["status"] == "success":
                chapter.status = "published"
                chapter.published_time = datetime.now()
                chapter.platform_chapter_id = publish_result.get("chapter_id")
                
                # 更新小说统计
                novel.total_chapters += 1
                novel.total_words += chapter.word_count
                
                db.commit()
                
                logger.info(f"✅ 章节 {chapter_id} 发布成功")
                return {"status": "success", "chapter_id": chapter_id}
            else:
                raise Exception(publish_result.get("error", "发布失败"))
                
        finally:
            loop.run_until_complete(publisher.close())
            loop.close()
        
    except Exception as exc:
        logger.error(f"自动发布章节失败: {exc}")
        chapter.status = "failed"
        chapter.error_message = str(exc)
        db.commit()
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def fetch_analytics_task(self, novel_id: int, days: int = 7):
    """
    抓取小说数据分析
    :param novel_id: 小说ID
    :param days: 抓取天数
    """
    db = SessionLocal()
    try:
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            return {"status": "error", "message": "Novel not found"}
        
        account = db.query(Account).filter(Account.id == novel.account_id).first()
        if not account:
            return {"status": "error", "message": "Account not found"}
        
        logger.info(f"开始抓取小说 {novel_id} 的数据分析")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        publisher = FanqiePublisher(account_id=account.id)
        
        try:
            loop.run_until_complete(
                publisher.initialize_with_cdp(cdp_port=9222)
            )
            
            if account.writer_cookies:
                loop.run_until_complete(
                    publisher.login_with_cookies(account.writer_cookies)
                )
            
            analytics_result = loop.run_until_complete(
                publisher.fetch_analytics(
                    novel_id=novel.platform_novel_id or "",
                    days=days
                )
            )
            
            if analytics_result["status"] == "success":
                data = analytics_result["data"]
                
                # 保存分析数据
                for i in range(days):
                    stat_date = datetime.now() - timedelta(days=i)
                    
                    analytics_record = FanqieAnalytics(
                        novel_id=novel_id,
                        stat_date=stat_date,
                        daily_reads=data.get("daily_reads", 0),
                        new_followers=data.get("new_followers", 0),
                        new_favorites=data.get("new_favorites", 0),
                        comments_count=data.get("comments_count", 0),
                        daily_ad_revenue=data.get("ad_revenue", 0.0),
                        completion_rate=data.get("completion_rate", 0.0),
                        retention_rate_day1=data.get("retention_rate_day1", 0.0),
                        retention_rate_day7=data.get("retention_rate_day7", 0.0),
                    )
                    
                    db.add(analytics_record)
                
                # 更新小说统计数据
                novel.total_reads = data.get("total_reads", novel.total_reads)
                novel.total_favorites = data.get("total_favorites", novel.total_favorites)
                novel.avg_rating = data.get("avg_rating", novel.avg_rating)
                
                db.commit()
                
                logger.info(f"✅ 小说 {novel_id} 数据抓取成功")
                return {"status": "success", "novel_id": novel_id}
            else:
                raise Exception(analytics_result.get("error", "数据抓取失败"))
                
        finally:
            loop.run_until_complete(publisher.close())
            loop.close()
        
    except Exception as exc:
        logger.error(f"数据抓取失败: {exc}")
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()


@celery_app.task
def check_consecutive_days_task():
    """
    检查所有番茄账号的断更情况
    如果连续未更新超过2天，发送预警
    """
    db = SessionLocal()
    try:
        logger.info("开始检查番茄账号断更情况")
        
        accounts = db.query(Account).filter(
            Account.platform == PlatformEnum.FANQIE
        ).all()
        
        warning_accounts = []
        
        for account in accounts:
            novels = db.query(Novel).filter(
                Novel.account_id == account.id,
                Novel.status == "serializing"
            ).all()
            
            for novel in novels:
                # 获取最后一章的发布时间
                last_chapter = db.query(Chapter).filter(
                    Chapter.novel_id == novel.id,
                    Chapter.status == "published"
                ).order_by(Chapter.published_time.desc()).first()
                
                if last_chapter and last_chapter.published_time:
                    days_since_update = (datetime.now() - last_chapter.published_time).days
                    
                    if days_since_update >= 2:
                        warning_accounts.append({
                            "account_id": account.id,
                            "account_name": account.username,
                            "novel_id": novel.id,
                            "novel_title": novel.title,
                            "days_since_update": days_since_update,
                            "last_update": last_chapter.published_time.isoformat()
                        })
                        
                        logger.warning(
                            f"⚠️  账号 {account.username} 的小说《{novel.title}》已断更{days_since_update}天"
                        )
        
        if warning_accounts:
            logger.warning(f"发现 {len(warning_accounts)} 个断更预警")
            
            # 发送通知（复用项目现有的报警系统）
            try:
                from app.services.operations.alert_system import AlertSystem
                alert_system = AlertSystem()
                
                for warning in warning_accounts:
                    message = (
                        f"⚠️ 断更预警\n"
                        f"账号：{warning['account_name']}\n"
                        f"小说：《{warning['novel_title']}》\n"
                        f"已断更：{warning['days_since_update']}天\n"
                        f"最后更新：{warning['last_update']}\n\n"
                        f"建议操作：\n"
                        f"1. 立即登录作家后台\n"
                        f"2. 发布新章节或设置定时发布\n"
                        f"3. 检查是否有其他异常"
                    )
                    
                    subject = f"断更预警：{warning['novel_title']}"
                    
                    # 并行发送邮件和钉钉通知
                    import asyncio
                    tasks = []
                    
                    # 添加邮件任务
                    tasks.append(
                        alert_system.send_email_alert(
                            subject=subject,
                            message=message
                        )
                    )
                    
                    # 添加钉钉任务
                    tasks.append(
                        alert_system.send_dingtalk_alert(message)
                    )
                    
                    # 执行通知
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                    loop.close()
                    
                    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
                    
                    if success_count > 0:
                        logger.info(f"✅ 已发送断更通知 ({success_count}/{len(tasks)}渠道): {warning['novel_title']}")
                    else:
                        logger.warning(f"⚠️  断更通知发送失败: {warning['novel_title']}")
                        
            except Exception as e:
                logger.error(f"发送通知失败: {e}")
                import traceback
                traceback.print_exc()
                # 即使通知失败，也不影响主流程
        
        logger.info("✅ 断更检查完成")
        return {
            "status": "success",
            "warning_count": len(warning_accounts),
            "warnings": warning_accounts
        }
        
    except Exception as e:
        logger.error(f"断更检查失败: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def update_income_stats_task():
    """
    更新所有番茄账号的收益统计
    """
    db = SessionLocal()
    try:
        logger.info("开始更新番茄账号收益统计")
        
        accounts = db.query(Account).filter(
            Account.platform == PlatformEnum.FANQIE
        ).all()
        
        for account in accounts:
            # 查询最近7天的收益数据
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            analytics_records = db.query(FanqieAnalytics).join(
                Novel, FanqieAnalytics.novel_id == Novel.id
            ).filter(
                Novel.account_id == account.id,
                FanqieAnalytics.stat_date >= seven_days_ago
            ).all()
            
            # 计算收益
            daily_income = sum(r.daily_ad_revenue for r in analytics_records) / 7 if analytics_records else 0
            monthly_income = daily_income * 30
            
            # 累计总收益
            all_analytics = db.query(FanqieAnalytics).join(
                Novel, FanqieAnalytics.novel_id == Novel.id
            ).filter(
                Novel.account_id == account.id
            ).all()
            
            total_income = sum(r.daily_ad_revenue for r in all_analytics)
            
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
def qualify_bonus_check_task():
    """
    检查番茄账号的全勤奖资格
    条件：连续30天日更4000字以上
    """
    db = SessionLocal()
    try:
        logger.info("开始检查番茄账号全勤奖资格")
        
        accounts = db.query(Account).filter(
            Account.platform == PlatformEnum.FANQIE
        ).all()
        
        qualified_accounts = []
        
        for account in accounts:
            novels = db.query(Novel).filter(
                Novel.account_id == account.id,
                Novel.status == "serializing"
            ).all()
            
            for novel in novels:
                # 检查最近30天的更新情况
                thirty_days_ago = datetime.now() - timedelta(days=30)
                
                chapters = db.query(Chapter).filter(
                    Chapter.novel_id == novel.id,
                    Chapter.status == "published",
                    Chapter.published_time >= thirty_days_ago
                ).all()
                
                # 统计每日字数
                daily_words = {}
                for chapter in chapters:
                    day = chapter.published_time.date()
                    if day not in daily_words:
                        daily_words[day] = 0
                    daily_words[day] += chapter.word_count
                
                # 检查是否每天都达到4000字
                consecutive_days = 0
                qualified = True
                
                for i in range(30):
                    check_date = (datetime.now() - timedelta(days=i)).date()
                    words = daily_words.get(check_date, 0)
                    
                    if words >= 4000:
                        consecutive_days += 1
                    else:
                        qualified = False
                        break
                
                if qualified and consecutive_days >= 30:
                    account.qualification_for_bonus = True
                    qualified_accounts.append({
                        "account_id": account.id,
                        "account_name": account.username,
                        "novel_id": novel.id,
                        "novel_title": novel.title,
                        "consecutive_days": consecutive_days
                    })
                    
                    logger.info(
                        f"✅ 账号 {account.username} 的小说《{novel.title}》"
                        f"满足全勤奖条件（连续{consecutive_days}天）"
                    )
                else:
                    account.qualification_for_bonus = False
                    account.consecutive_days = consecutive_days
        
        db.commit()
        
        logger.info(f"✅ 全勤奖检查完成，{len(qualified_accounts)} 个账号符合条件")
        return {
            "status": "success",
            "qualified_count": len(qualified_accounts),
            "qualified_accounts": qualified_accounts
        }
        
    except Exception as e:
        logger.error(f"全勤奖检查失败: {e}")
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()
