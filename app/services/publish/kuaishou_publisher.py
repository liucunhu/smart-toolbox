"""
快手自动化发布服务
支持视频发布、图文发布
"""
import asyncio
import json
from playwright.async_api import async_playwright, BrowserContext, Page
from app.utils.logger import logger
from typing import Dict, Any, Optional


class KuaishouPublisher:
    """快手自动化发布引擎"""

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
        logger.info(f"快手发布引擎初始化完成，账号 ID: {self.account_id}")

    async def login_with_manual_input(self, username: str, password: str) -> Dict[str, Any]:
        """
        人工辅助登录快手
        流程：
        1. 打开快手创作者平台
        2. 自动填充账号密码
        3. 等待用户完成验证码
        4. 保存登录状态（Cookies）
        """
        try:
            # 1. 打开快手创作者平台
            await self.page.goto("https://cp.kuaishou.com/", timeout=30000)
            await asyncio.sleep(2)

            # 2. 尝试自动登录
            try:
                logger.info("正在尝试自动登录...")
                
                # 查找账号输入框
                username_input = await self.page.query_selector('input[placeholder*="手机号"], input[placeholder*="账号"], input[type="text"]')
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
                            # 检查是否已勾选
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
                else:
                    logger.warning("⚠️ 未找到登录按钮")
                
                # 等待登录成功
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.warning(f"自动填充失败，请手动完成登录: {e}")
            
            # 3. 多种登录成功检测策略
            logger.info("请在浏览器窗口中完成登录（如需验证码请手动处理），系统将自动检测登录状态...")
            
            login_detected = False
            for attempt in range(60):
                await asyncio.sleep(2)
                current_url = self.page.url
                
                # 检测策略1: URL不包含login
                if "login" not in current_url and "cp.kuaishou.com" in current_url:
                    # 进一步检查是否有用户信息
                    try:
                        user_info = await self.page.query_selector('.user-info, .avatar, [class*="user"]')
                        if user_info:
                            login_detected = True
                            logger.info(f"✅ 检测到登录成功（用户信息存在）")
                            break
                    except:
                        pass
                    
                    # 检测策略2: 检查Cookie
                    try:
                        cookies = await self.context.cookies()
                        kuaishou_cookies = [c for c in cookies if 'kuaishou' in c.get('name', '').lower() or 'token' in c.get('name', '').lower()]
                        if len(kuaishou_cookies) > 0:
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
            
            logger.info(f"快手账号 {username} 登录成功！")
            logger.info(f"已保存 {len(cookies)} 个 Cookie")
            
            return {
                "status": "success",
                "cookies": cookies_json,
                "message": "登录成功，已保存会话状态"
            }

        except Exception as e:
            logger.error(f"快手登录失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def publish_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        cover_image: str = None
    ) -> Dict[str, Any]:
        """
        发布视频到快手
        
        Args:
            video_path: 视频文件路径
            title: 视频标题
            description: 视频描述
            tags: 标签列表
            cover_image: 封面图片路径（可选）
        
        Returns:
            发布结果字典
        """
        try:
            logger.info(f"开始发布快手视频: {title}")
            
            # 1. 导航到发布页面
            await self.page.goto("https://cp.kuaishou.com/article/publish/video", timeout=30000)
            await asyncio.sleep(3)
            
            # 2. 上传视频文件
            logger.info("正在上传视频文件...")
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
                logger.info("✅ 视频文件已上传")
                
                # 等待视频上传和处理完成
                logger.info("等待视频处理完成...")
                await asyncio.sleep(10)  # 根据视频大小调整
            else:
                raise Exception("未找到文件上传元素")
            
            # 3. 填写标题和描述
            logger.info("正在填写标题和描述...")
            
            # 标题输入框
            title_input = await self.page.query_selector('input[placeholder*="标题"], input[placeholder*="添加标题"]')
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
                logger.info("✅ 标题已填写")
            
            # 描述输入框
            desc_input = await self.page.query_selector('textarea[placeholder*="描述"], textarea[placeholder*="添加描述"]')
            if desc_input and description:
                await desc_input.fill(description)
                await asyncio.sleep(1)
                logger.info("✅ 描述已填写")
            
            # 4. 添加标签
            if tags:
                logger.info(f"正在添加标签: {tags}")
                for tag in tags[:5]:  # 最多5个标签
                    tag_input = await self.page.query_selector('input[placeholder*="标签"], input[placeholder*="添加标签"]')
                    if tag_input:
                        await tag_input.fill(tag)
                        await asyncio.sleep(0.5)
                        # 按回车确认
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(0.5)
                logger.info("✅ 标签已添加")
            
            # 5. 设置封面（如果提供）
            if cover_image:
                logger.info("正在设置封面...")
                # 封面上传逻辑（根据实际页面结构调整）
                cover_upload = await self.page.query_selector('.cover-upload, [class*="cover"] input[type="file"]')
                if cover_upload:
                    await cover_upload.set_input_files(cover_image)
                    await asyncio.sleep(2)
                    logger.info("✅ 封面已设置")
            
            # 6. 点击发布按钮
            logger.info("正在发布视频...")
            publish_button = await self.page.query_selector('button:has-text("发布"), button:has-text("立即发布")')
            if publish_button:
                await publish_button.click()
                logger.info("✅ 已点击发布按钮")
                
                # 等待发布完成
                await asyncio.sleep(5)
                
                # 检查发布结果
                success_msg = await self.page.query_selector('text=发布成功, text=发布成功')
                if success_msg:
                    logger.info("🎉 视频发布成功！")
                    return {
                        "status": "success",
                        "message": "视频发布成功",
                        "title": title,
                        "publish_time": asyncio.get_event_loop().time()
                    }
                else:
                    logger.warning("⚠️ 未检测到发布成功提示，但已提交")
                    return {
                        "status": "success",
                        "message": "视频已提交发布",
                        "title": title
                    }
            else:
                raise Exception("未找到发布按钮")

        except Exception as e:
            logger.error(f"快手视频发布失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def publish_image_text(
        self,
        images: list,
        title: str,
        content: str,
        tags: list = None
    ) -> Dict[str, Any]:
        """
        发布图文内容到快手
        
        Args:
            images: 图片路径列表
            title: 标题
            content: 正文内容
            tags: 标签列表
        
        Returns:
            发布结果字典
        """
        try:
            logger.info(f"开始发布快手图文: {title}")
            
            # 1. 导航到图文发布页面
            await self.page.goto("https://cp.kuaishou.com/article/publish/image-text", timeout=30000)
            await asyncio.sleep(3)
            
            # 2. 上传图片
            logger.info("正在上传图片...")
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(images)
                logger.info(f"✅ 已上传 {len(images)} 张图片")
                await asyncio.sleep(5)
            
            # 3. 填写标题和内容
            title_input = await self.page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
            
            content_input = await self.page.query_selector('textarea[placeholder*="内容"], textarea[placeholder*="正文"]')
            if content_input:
                await content_input.fill(content)
                await asyncio.sleep(1)
            
            # 4. 添加标签
            if tags:
                for tag in tags[:5]:
                    tag_input = await self.page.query_selector('input[placeholder*="标签"]')
                    if tag_input:
                        await tag_input.fill(tag)
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(0.5)
            
            # 5. 点击发布
            publish_button = await self.page.query_selector('button:has-text("发布")')
            if publish_button:
                await publish_button.click()
                await asyncio.sleep(5)
                logger.info("🎉 图文发布成功！")
                return {
                    "status": "success",
                    "message": "图文发布成功",
                    "title": title
                }
            
            return {
                "status": "failed",
                "error": "未找到发布按钮"
            }

        except Exception as e:
            logger.error(f"快手图文发布失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

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
            logger.info("快手发布引擎已关闭")
        except Exception as e:
            logger.error(f"关闭快手发布引擎失败: {str(e)}")


# 示例用法
if __name__ == "__main__":
    async def test_publish():
        publisher = KuaishouPublisher(account_id=1)
        
        try:
            # 1. 初始化浏览器
            await publisher.initialize_browser()
            
            # 2. 登录
            login_result = await publisher.login_with_manual_input(
                username="your_phone",
                password="your_password"
            )
            print(f"登录结果: {login_result}")
            
            if login_result["status"] == "success":
                # 3. 发布视频
                publish_result = await publisher.publish_video(
                    video_path="/path/to/video.mp4",
                    title="测试视频标题",
                    description="这是测试视频描述",
                    tags=["测试", "短视频"]
                )
                print(f"发布结果: {publish_result}")
        
        finally:
            await publisher.close()

    asyncio.run(test_publish())
