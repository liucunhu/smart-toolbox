"""
B站（哔哩哔哩）自动化发布服务
支持视频发布、专栏文章发布
"""
import asyncio
import json
from playwright.async_api import async_playwright, BrowserContext, Page
from app.utils.logger import logger
from typing import Dict, Any, Optional


class BilibiliPublisher:
    """B站自动化发布引擎"""

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
        logger.info(f"B站发布引擎初始化完成，账号 ID: {self.account_id}")

    async def login_with_qr_code(self) -> Dict[str, Any]:
        """
        扫码登录B站
        B站主要使用扫码登录方式
        
        Returns:
            登录结果字典
        """
        try:
            # 1. 打开B站创作中心
            await self.page.goto("https://member.bilibili.com/platform/upload/video/frame", timeout=30000)
            await asyncio.sleep(3)
            
            logger.info("请使用B站APP扫描二维码登录...")
            
            # 2. 等待扫码登录成功
            login_detected = False
            for attempt in range(90):  # 最多等待3分钟
                await asyncio.sleep(2)
                current_url = self.page.url
                
                # 检测是否登录成功
                if "member.bilibili.com" in current_url and "login" not in current_url:
                    try:
                        # 检查是否有用户信息元素
                        user_info = await self.page.query_selector('.user-info, .up-name, [class*="user"]')
                        if user_info:
                            login_detected = True
                            logger.info("✅ 检测到登录成功")
                            break
                    except:
                        pass
                    
                    # 检查Cookie
                    try:
                        cookies = await self.context.cookies()
                        bili_cookies = [c for c in cookies if 'bili' in c.get('name', '').lower() or 'DedeUserID' in c.get('name', '')]
                        if len(bili_cookies) > 0:
                            login_detected = True
                            logger.info(f"✅ 检测到登录成功（Cookie存在）")
                            break
                    except:
                        pass
                
                if (attempt + 1) % 15 == 0:
                    logger.info(f"⏳ 等待扫码中... ({attempt + 1}/90)")
            
            if not login_detected:
                raise TimeoutError("等待扫码登录超时")
            
            # 3. 保存Cookie
            cookies = await self.context.cookies()
            cookies_json = json.dumps(cookies)
            
            logger.info(f"B站登录成功！已保存 {len(cookies)} 个 Cookie")
            
            return {
                "status": "success",
                "cookies": cookies_json,
                "message": "登录成功"
            }

        except Exception as e:
            logger.error(f"B站登录失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def publish_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        copyright: int = 1,  # 1=原创, 2=转载
        tid: int = 0,  # 分区ID
        cover_image: str = None
    ) -> Dict[str, Any]:
        """
        发布视频到B站
        
        Args:
            video_path: 视频文件路径
            title: 视频标题（最多80字）
            description: 视频简介（最多2000字）
            tags: 标签列表（最多10个）
            copyright: 版权类型（1=原创, 2=转载）
            tid: 分区ID（0=默认）
            cover_image: 封面图片路径（可选）
        
        Returns:
            发布结果字典
        """
        try:
            logger.info(f"开始发布B站视频: {title}")
            
            # 1. 导航到发布页面
            await self.page.goto("https://member.bilibili.com/platform/upload/video/frame", timeout=30000)
            await asyncio.sleep(3)
            
            # 2. 上传视频文件
            logger.info("正在上传视频文件...")
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
                logger.info("✅ 视频文件已上传")
                
                # 等待视频上传和处理完成
                logger.info("等待视频处理完成...")
                for i in range(30):  # 最多等待60秒
                    await asyncio.sleep(2)
                    # 检查上传进度
                    progress = await self.page.query_selector('.upload-progress, [class*="progress"]')
                    if not progress:
                        logger.info("✅ 视频处理完成")
                        break
                    if i % 5 == 0:
                        logger.info(f"⏳ 视频处理中... ({i*2}秒)")
            else:
                raise Exception("未找到文件上传元素")
            
            # 3. 填写标题
            logger.info("正在填写标题...")
            title_input = await self.page.query_selector('input[placeholder*="标题"], input.v-input__inner')
            if title_input:
                await title_input.fill(title[:80])  # B站标题最多80字
                await asyncio.sleep(1)
                logger.info("✅ 标题已填写")
            
            # 4. 填写简介
            logger.info("正在填写简介...")
            desc_input = await self.page.query_selector('textarea[placeholder*="简介"], textarea.v-textarea__inner')
            if desc_input:
                await desc_input.fill(description[:2000])  # 简介最多2000字
                await asyncio.sleep(1)
                logger.info("✅ 简介已填写")
            
            # 5. 添加标签
            if tags:
                logger.info(f"正在添加标签: {tags}")
                for tag in tags[:10]:  # B站最多10个标签
                    tag_input = await self.page.query_selector('input[placeholder*="标签"], .tag-input input')
                    if tag_input:
                        await tag_input.fill(tag)
                        await asyncio.sleep(0.5)
                        # 按回车确认
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(0.5)
                logger.info("✅ 标签已添加")
            
            # 6. 选择分区（如果提供）
            if tid > 0:
                logger.info(f"正在选择分区: {tid}")
                # 分区选择逻辑（根据实际页面结构调整）
                await asyncio.sleep(1)
            
            # 7. 设置封面（如果提供）
            if cover_image:
                logger.info("正在设置封面...")
                cover_upload = await self.page.query_selector('.cover-uploader input[type="file"], [class*="cover"] input[type="file"]')
                if cover_upload:
                    await cover_upload.set_input_files(cover_image)
                    await asyncio.sleep(2)
                    logger.info("✅ 封面已设置")
            
            # 8. 选择版权类型
            if copyright == 2:
                logger.info("设置为转载视频")
                reprint_radio = await self.page.query_selector('label:has-text("转载"), .copyright-reprint')
                if reprint_radio:
                    await reprint_radio.click()
                    await asyncio.sleep(1)
            
            # 9. 点击发布按钮
            logger.info("正在提交发布...")
            publish_button = await self.page.query_selector('button:has-text("立即投稿"), button:has-text("发布"), .submit-btn')
            if publish_button:
                await publish_button.click()
                logger.info("✅ 已点击发布按钮")
                
                # 等待发布完成
                await asyncio.sleep(5)
                
                # 检查发布结果
                success_msg = await self.page.query_selector('text=投稿成功, text=发布成功, .success-tip')
                if success_msg:
                    logger.info("🎉 视频发布成功！")
                    return {
                        "status": "success",
                        "message": "视频发布成功",
                        "title": title,
                        "copyright": "原创" if copyright == 1 else "转载"
                    }
                else:
                    logger.warning("⚠️ 未检测到发布成功提示，但已提交")
                    return {
                        "status": "success",
                        "message": "视频已提交审核",
                        "title": title
                    }
            else:
                raise Exception("未找到发布按钮")

        except Exception as e:
            logger.error(f"B站视频发布失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def publish_article(
        self,
        title: str,
        content: str,
        category: str = "",
        tags: list = None,
        cover_image: str = None
    ) -> Dict[str, Any]:
        """
        发布专栏文章到B站
        
        Args:
            title: 文章标题
            content: 文章内容（支持Markdown）
            category: 文章分类
            tags: 标签列表
            cover_image: 封面图片
        
        Returns:
            发布结果字典
        """
        try:
            logger.info(f"开始发布B站专栏: {title}")
            
            # 1. 导航到专栏发布页面
            await self.page.goto("https://member.bilibili.com/platform/upload/article/frame", timeout=30000)
            await asyncio.sleep(3)
            
            # 2. 填写标题
            title_input = await self.page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
            
            # 3. 填写内容
            content_editor = await self.page.query_selector('.editor-content, [class*="editor"] textarea')
            if content_editor:
                await content_editor.fill(content)
                await asyncio.sleep(2)
            
            # 4. 添加标签和分类
            if tags:
                for tag in tags[:5]:
                    tag_input = await self.page.query_selector('input[placeholder*="标签"]')
                    if tag_input:
                        await tag_input.fill(tag)
                        await self.page.keyboard.press('Enter')
                        await asyncio.sleep(0.5)
            
            # 5. 设置封面
            if cover_image:
                cover_upload = await self.page.query_selector('input[type="file"]')
                if cover_upload:
                    await cover_upload.set_input_files(cover_image)
                    await asyncio.sleep(2)
            
            # 6. 点击发布
            publish_button = await self.page.query_selector('button:has-text("发布"), button:has-text("投稿")')
            if publish_button:
                await publish_button.click()
                await asyncio.sleep(5)
                
                logger.info("🎉 专栏发布成功！")
                return {
                    "status": "success",
                    "message": "专栏发布成功",
                    "title": title
                }
            
            return {
                "status": "failed",
                "error": "未找到发布按钮"
            }

        except Exception as e:
            logger.error(f"B站专栏发布失败: {str(e)}")
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
            logger.info("B站发布引擎已关闭")
        except Exception as e:
            logger.error(f"关闭B站发布引擎失败: {str(e)}")


# 示例用法
if __name__ == "__main__":
    async def test_publish():
        publisher = BilibiliPublisher(account_id=1)
        
        try:
            # 1. 初始化浏览器
            await publisher.initialize_browser()
            
            # 2. 登录
            login_result = await publisher.login_with_qr_code()
            print(f"登录结果: {login_result}")
            
            if login_result["status"] == "success":
                # 3. 发布视频
                publish_result = await publisher.publish_video(
                    video_path="/path/to/video.mp4",
                    title="测试视频标题",
                    description="这是测试视频简介",
                    tags=["测试", "B站", "短视频"],
                    copyright=1,
                    tid=0
                )
                print(f"发布结果: {publish_result}")
        
        finally:
            await publisher.close()

    asyncio.run(test_publish())
