"""
带网络响应捕获的头条发布测试
"""
import asyncio
import json
from playwright.async_api import async_playwright
from app.utils.logger import logger


async def test_with_response_capture():
    """测试并发布，同时捕获网络响应"""
    
    print("="*80)
    print("🧪 头条发布测试（带响应捕获）")
    print("="*80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()
    
    # 存储所有响应
    responses = {}
    
    def handle_response(response):
        url = response.url
        if 'publish' in url or 'article' in url:
            status = response.status
            try:
                body = response.body()
                responses[url] = {
                    'status': status,
                    'body': body
                }
                logger.info(f"📥 捕获响应: {url[:80]}... (状态: {status})")
            except Exception as e:
                logger.warning(f"无法读取响应体: {e}")
    
    page.on("response", handle_response)
    
    try:
        # 步骤 1: 登录
        print("\n[步骤 1] 请登录头条...")
        await page.goto("https://mp.toutiao.com/", timeout=30000)
        
        if "login" in page.url:
            print("⚠️  请在浏览器中完成登录，然后按回车继续...")
            input()
        else:
            print("✅ 已登录")
        
        # 步骤 2: 进入发布页面
        print("\n[步骤 2] 进入发布页面...")
        await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", timeout=30000)
        await asyncio.sleep(3)
        
        # 步骤 3: 填写标题
        print("\n[步骤 3] 填写标题...")
        title_input = await page.query_selector('input[placeholder="请输入标题"]')
        if title_input:
            test_title = f"测试_{int(asyncio.get_event_loop().time())}"
            await title_input.fill(test_title)
            print(f"✅ 标题: {test_title}")
        else:
            print("❌ 未找到标题输入框")
            return
        
        # 步骤 4: 填写内容（使用更长的内容）
        print("\n[步骤 4] 填写内容...")
        editor = await page.query_selector('div[contenteditable="true"]')
        if editor:
            test_content = """这是一篇测试文章，用于验证头条发布功能。

今日头条是中国领先的个性化信息聚合平台，拥有数亿活跃用户。
在这个平台上发布优质内容，可以触达大量潜在读者，获得流量和收益。

自动化发布工具可以帮助创作者提高效率，节省时间。
通过Playwright等浏览器自动化技术，我们可以模拟人工操作，
实现自动登录、自动填写表单、自动发布等功能。

本次测试的目的是验证完整的发布流程是否正常工作。
如果这篇文章成功发布，说明我们的自动化脚本已经可以正常使用。

文章内容需要足够长，以满足平台的最低要求。
通常建议文章至少在500字以上，这样更容易通过审核。

希望这次测试能够成功！感谢你的耐心。
"""
            await editor.fill(test_content)
            print(f"✅ 内容长度: {len(test_content)} 字")
        else:
            print("❌ 未找到编辑器")
            return
        
        await asyncio.sleep(2)
        
        # 步骤 5: 点击发布并捕获响应
        print("\n[步骤 5] 点击发布按钮...")
        publish_button = await page.query_selector('button:has-text("发布")')
        if publish_button:
            await publish_button.click()
            print("✅ 已点击发布")
            
            # 等待响应
            print("⏳ 等待网络响应...")
            await asyncio.sleep(10)
            
            # 保存响应
            if responses:
                response_file = "logs/publish_response.json"
                with open(response_file, 'w', encoding='utf-8') as f:
                    json.dump(responses, f, ensure_ascii=False, indent=2)
                print(f"✅ 响应已保存到: {response_file}")
                
                # 打印响应内容
                for url, data in responses.items():
                    print(f"\n{'='*80}")
                    print(f"URL: {url[:100]}")
                    print(f"状态码: {data['status']}")
                    try:
                        body_text = data['body'].decode('utf-8')
                        print(f"响应内容: {body_text[:500]}")
                    except:
                        print(f"响应内容: <二进制数据>")
                    print(f"{'='*80}")
            else:
                print("⚠️  未捕获到任何响应")
        else:
            print("❌ 未找到发布按钮")
        
        print("\n⏸️  浏览器将保持打开，请检查页面状态")
        print("   按回车关闭浏览器...")
        input()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏸️  按回车关闭浏览器...")
        input()
    finally:
        await browser.close()
        await playwright.stop()
        print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_with_response_capture())
