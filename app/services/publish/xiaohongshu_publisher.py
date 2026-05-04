"""
小红书自动化发布服务
支持图文笔记、视频笔记发布
"""
import asyncio
import json
from playwright.async_api import async_playwright, BrowserContext, Page
from app.utils.logger import logger
from typing import Dict, Any, Optional


class XiaohongshuPublisher:
    """小红书自动化发布引擎"""

    def __init__(self, account_id: int):
        self.account_id = account_id
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize_browser(self, headless: bool = False):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()
        logger.info(f"小红书发布引擎初始化完成，账号 ID: {self.account_id}")

    async def login_with_password(self, username: str, password: str) -> Dict[str, Any]:
        """
        密码登录小红书创作者平台
        
        Args:
            username: 手机号或邮箱
            password: 密码
        
        Returns:
            登录结果字典
        """
        try:
            # 1. 打开小红书创作者平台登录页
            await self.page.goto("https://creator.xiaohongshu.com/login", timeout=30000)
            await asyncio.sleep(2)

            # 2. 尝试自动登录
            try:
                logger.info("正在尝试自动登录...")
                
                # 切换到密码登录（如果需要）
                password_login_btn = await self.page.query_selector('text=密码登录, text=账号密码登录')
                if password_login_btn:
                    await password_login_btn.click()
                    await asyncio.sleep(2)
                    logger.info("✅ 已切换到密码登录模式")
                
                # 查找账号输入框
                username_input = await self.page.query_selector('input[placeholder*="手机号"], input[placeholder*="邮箱"], input[type="text"]')
                if username_input:
                    await username_input.fill(username)
                    await asyncio.sleep(1)
                    logger.info(f"✅ 已填充账号: {username}")
                else:
                    logger.warning("⚠️ 未找到账号输入框")
                
                # 查找密码输入框
                password_input = await self.page.query_selector('input[type="password"]')
                if password_input:
                    await password_input.fill(password)
                    await asyncio.sleep(1)
                    logger.info("✅ 已填充密码")
                else:
                    logger.warning("⚠️ 未找到密码输入框")

                # ★★★ 关键：自动勾选用户协议 ★★★
                logger.info("正在查找并勾选用户协议...")
                agreement_selectors = [
                    'input[type="checkbox"]',
                    'label:has-text("用户协议")',
                    'label:has-text("我已阅读并同意")',
                    'label:has-text("隐私政策")',
                    '[class*="agree"] input[type="checkbox"]',
                    '[class*="protocol"] input[type="checkbox"]',
                    'input[name*="agree"]',
                    'input[name*="protocol"]',
                    '.agreement-checkbox input[type="checkbox"]'
                ]
                
                agreement_checked = False
                for selector in agreement_selectors:
                    try:
                        agreement_checkbox = await self.page.query_selector(selector)
                        if agreement_checkbox:
                            is_checked = await agreement_checkbox.is_checked()
                            if not is_checked:
                                await agreement_checkbox.check()
                                logger.info("✅ 已自动勾选用户协议")
                            else:
                                logger.info("用户协议已勾选")
                            agreement_checked = True
                            await asyncio.sleep(0.5)
                            break
                    except:
                        continue
                
                if not agreement_checked:
                    logger.warning("⚠️ 未找到用户协议复选框，尝试继续登录")

                # 点击登录按钮
                login_button = await self.page.query_selector('button:has-text("登录"), button[type="submit"]')
                if login_button:
                    await login_button.click()
                    logger.info("✅ 已点击登录按钮")
                    
                    # 等待登录成功
                    await asyncio.sleep(3)
                else:
                    logger.warning("⚠️ 未找到登录按钮")
                
            except Exception as e:
                logger.warning(f"自动填充失败，请手动完成登录: {e}")
            
            # 3. 多种登录成功检测策略
            logger.info("请在浏览器窗口中完成登录（如需验证码请手动处理），系统将自动检测登录状态...")
            
            login_detected = False
            for attempt in range(60):
                await asyncio.sleep(2)
                current_url = self.page.url
                
                # 检测策略1: URL不包含login且包含creator
                if "creator.xiaohongshu.com" in current_url and "login" not in current_url:
                    try:
                        # 检查是否有用户信息
                        user_info = await self.page.query_selector('.user-info, .nickname, [class*="user"]')
                        if user_info:
                            login_detected = True
                            logger.info("✅ 检测到登录成功（用户信息存在）")
                            break
                    except:
                        pass
                    
                    # 检测策略2: 检查Cookie
                    try:
                        cookies = await self.context.cookies()
                        xhs_cookies = [c for c in cookies if 'xhs' in c.get('name', '').lower() or 'token' in c.get('name', '').lower()]
                        if len(xhs_cookies) > 0:
                            login_detected = True
                            logger.info(f"✅ 检测到登录成功（Cookie存在）")
                            break
                    except:
                        pass
                
                if (attempt + 1) % 10 == 0:
                    logger.info(f"⏳ 等待登录中... ({attempt + 1}/60)")
            
            if not login_detected:
                raise TimeoutError("等待登录超时，请确认是否已完成登录操作")

            # 4. 保存登录状态
            cookies = await self.context.cookies()
            cookies_json = json.dumps(cookies)
            
            logger.info(f"小红书账号 {username} 登录成功！")
            logger.info(f"已保存 {len(cookies)} 个 Cookie")
            
            return {
                "status": "success",
                "cookies": cookies_json,
                "message": "登录成功，已保存会话状态"
            }

        except Exception as e:
            logger.error(f"小红书登录失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def publish_note(
        self,
        images: list,
        title: str,
        content: str,
        tags: list = None,
        note_type: str = "normal"  # normal=图文, video=视频
    ) -> Dict[str, Any]:
        """
        发布笔记到小红书
        
        Args:
            images: 图片路径列表（最多9张）或视频路径
            title: 标题（最多20字）
            content: 正文内容（最多1000字）
            tags: 话题标签列表（最多10个）
            note_type: 笔记类型（normal=图文, video=视频）
        
        Returns:
            发布结果字典
        """
        try:
            logger.info(f"开始发布小红书笔记: {title}")
            
            # 1. 导航到发布页面
            if note_type == "video":
                await self.page.goto("https://creator.xiaohongshu.com/publish/publish?containerType=video", timeout=30000)
            else:
                await self.page.goto("https://creator.xiaohongshu.com/publish/publish", timeout=30000)
            await asyncio.sleep(3)
            
            # 2. 上传图片/视频
            logger.info(f"正在上传{'图片' if note_type == 'normal' else '视频'}...")
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                if note_type == "normal" and isinstance(images, list):
                    # 图文笔记：上传多张图片
                    await file_input.set_input_files(images[:9])  # 最多9张
                    logger.info(f"✅ 已上传 {len(images)} 张图片")
                else:
                    # 视频笔记：上传单个视频
                    video_path = images if isinstance(images, str) else images[0]
                    await file_input.set_input_files(video_path)
                    logger.info("✅ 视频已上传")
                
                # 等待上传完成
                await asyncio.sleep(5)
            else:
                raise Exception("未找到文件上传元素")
            
            # 3. 填写标题
            logger.info("正在填写标题...")
            title_input = await self.page.query_selector('input[placeholder*="标题"], input[class*="title"]')
            if title_input:
                await title_input.fill(title[:20])  # 小红书标题最多20字
                await asyncio.sleep(1)
                logger.info("✅ 标题已填写")
            
            # 4. 填写正文
            logger.info("正在填写正文...")
            content_input = await self.page.query_selector('textarea[placeholder*="正文"], textarea[placeholder*="添加正文"], .editor-content')
            if content_input:
                # 智能插入Emoji（小红书特色）
                enhanced_content = self._add_emojis(content[:1000])  # 最多1000字
                await content_input.fill(enhanced_content)
                await asyncio.sleep(1)
                logger.info("✅ 正文已填写")
            
            # 5. 添加话题标签
            if tags:
                logger.info(f"正在添加话题标签: {tags}")
                for tag in tags[:10]:  # 最多10个标签
                    # 在正文中添加 #标签
                    await content_input.press('End')
                    await content_input.press('Space')
                    await content_input.type(f'#{tag}')
                    await asyncio.sleep(0.5)
                logger.info("✅ 标签已添加")
            
            # 6. 添加地点（可选）
            # TODO: 实现地点选择
            
            # 7. 点击发布按钮
            logger.info("正在提交发布...")
            publish_button = await self.page.query_selector('button:has-text("发布笔记"), button:has-text("立即发布"), .publish-btn')
            if publish_button:
                await publish_button.click()
                logger.info("✅ 已点击发布按钮")
                
                # 等待发布完成
                await asyncio.sleep(5)
                
                # 检查发布结果
                success_msg = await self.page.query_selector('text=发布成功, .success-tip')
                if success_msg:
                    logger.info("🎉 笔记发布成功！")
                    return {
                        "status": "success",
                        "message": "笔记发布成功",
                        "title": title,
                        "note_type": note_type,
                        "image_count": len(images) if isinstance(images, list) else 1
                    }
                else:
                    logger.warning("⚠️ 未检测到发布成功提示，但已提交")
                    return {
                        "status": "success",
                        "message": "笔记已提交发布",
                        "title": title
                    }
            else:
                raise Exception("未找到发布按钮")

        except Exception as e:
            logger.error(f"小红书笔记发布失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _add_emojis(self, text: str) -> str:
        """
        智能添加Emoji到文本（小红书风格）
        
        Args:
            text: 原始文本
        
        Returns:
            添加了Emoji的文本
        """
        # 小红书常用的Emoji列表
        emojis = ['✨', '💕', '🌟', '💖', '🎀', '🌸', '💫', '⭐', '🔥', '❤️']
        
        # 在段落开头添加Emoji
        lines = text.split('\n')
        enhanced_lines = []
        for i, line in enumerate(lines):
            if line.strip():  # 非空行
                emoji = emojis[i % len(emojis)]
                enhanced_lines.append(f"{emoji} {line}")
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("小红书发布引擎已关闭")
        except Exception as e:
            logger.error(f"关闭小红书发布引擎失败: {str(e)}")


# 示例用法
if __name__ == "__main__":
    async def test_publish():
        publisher = XiaohongshuPublisher(account_id=1)
        
        try:
            # 1. 初始化浏览器
            await publisher.initialize_browser()
            
            # 2. 登录
            login_result = await publisher.login_with_password(
                username="your_phone",
                password="your_password"
            )
            print(f"登录结果: {login_result}")
            
            if login_result["status"] == "success":
                # 3. 发布图文笔记
                publish_result = await publisher.publish_note(
                    images=["/path/to/image1.jpg", "/path/to/image2.jpg"],
                    title="测试笔记标题",
                    content="这是测试笔记内容，分享好物给大家！",
                    tags=["好物分享", "生活记录", "日常"],
                    note_type="normal"
                )
                print(f"发布结果: {publish_result}")
        
        finally:
            await publisher.close()

    asyncio.run(test_publish())
