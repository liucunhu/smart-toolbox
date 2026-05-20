"""
智能头条发布测试 - 处理iframe和动态加载
"""
import asyncio
from playwright.async_api import async_playwright


async def smart_publish_test():
    """智能发布测试"""
    
    print("="*80)
    print("🧠 智能头条发布测试")
    print("="*80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()
    
    try:
        # 步骤 1: 登录
        print("\n[步骤 1] 登录...")
        await page.goto("https://mp.toutiao.com/", timeout=30000)
        
        if "login" in page.url:
            print("⚠️  请手动完成登录，然后按回车...")
            input()
        else:
            print("✅ 已登录")
        
        # 步骤 2: 打开发布页面
        print("\n[步骤 2] 打开发布页面...")
        publish_url = "https://mp.toutiao.com/profile_v4/graphic/publish?from=toutiao_pc"
        await page.goto(publish_url, timeout=30000)
        
        # 等待页面完全加载
        print("⏳ 等待页面加载...")
        try:
            await page.wait_for_load_state('domcontentloaded', timeout=15000)
        except:
            print("   ⚠️  domcontentloaded超时，继续执行")
        
        await asyncio.sleep(5)  # 额外等待5秒让JS执行
        
        print(f"✅ 页面已加载，URL: {page.url}")
        
        # 步骤 3: 查找并填写标题
        print("\n[步骤 3] 查找标题输入框...")
        
        # 尝试多种选择器
        title_selectors = [
            'input[placeholder*="标题"]',
            'input[placeholder*="请输入标题"]',
            'textarea[placeholder*="标题"]',
            'input[name="title"]',
            '#titleInput',
            '.title-input',
            '[class*="title"] input'
        ]
        
        title_input = None
        for selector in title_selectors:
            try:
                title_input = await page.query_selector(selector)
                if title_input and await title_input.is_visible():
                    print(f"✅ 找到标题输入框: {selector}")
                    break
            except Exception as e:
                print(f"  选择器 {selector} 失败: {e}")
        
        if not title_input:
            # 尝试在iframe中查找
            print("⚠️  在主页面未找到，尝试在iframe中查找...")
            frames = page.frames
            print(f"   页面共有 {len(frames)} 个frame")
            
            for i, frame in enumerate(frames):
                print(f"   检查 frame[{i}]: {frame.url[:80]}...")
                for selector in title_selectors:
                    try:
                        title_input = await frame.query_selector(selector)
                        if title_input and await title_input.is_visible():
                            print(f"   ✅ 在frame[{i}]中找到: {selector}")
                            # 切换到这个frame进行操作
                            page = frame
                            break
                    except:
                        continue
                if title_input:
                    break
        
        if title_input:
            test_title = f"智能测试_{int(asyncio.get_event_loop().time())}"
            await title_input.fill(test_title)
            await asyncio.sleep(1)
            
            # 验证是否填写成功
            value = await title_input.input_value()
            if value == test_title:
                print(f"✅ 标题填写成功: {test_title}")
            else:
                print(f"⚠️  标题可能未正确填写，期望: {test_title}, 实际: {value}")
        else:
            print("❌ 未找到标题输入框！")
            print("\n💡 调试信息:")
            print(f"   当前URL: {page.url}")
            print(f"   页面标题: {await page.title()}")
            
            # 保存HTML
            html_file = f"logs/smart_test_no_title_{int(asyncio.get_event_loop().time())}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(await page.content())
            print(f"   HTML已保存: {html_file}")
            
            # 列出所有输入框
            inputs = await page.query_selector_all('input, textarea')
            print(f"   页面上有 {len(inputs)} 个输入框")
            for i, inp in enumerate(inputs[:10]):
                placeholder = await inp.get_attribute('placeholder')
                name = await inp.get_attribute('name')
                input_type = await inp.get_attribute('type')
                print(f"     [{i}] type={input_type}, placeholder={placeholder}, name={name}")
            
            return
        
        # 步骤 4: 查找并填写内容
        print("\n[步骤 4] 查找内容编辑器...")
        
        editor_selectors = [
            'div[contenteditable="true"]',
            'div[class*="editor"]',
            'iframe[class*="editor"]',
            '.ql-editor',
            '[class*="content"] div[contenteditable]'
        ]
        
        editor = None
        for selector in editor_selectors:
            try:
                editor = await page.query_selector(selector)
                if editor and await editor.is_visible():
                    print(f"✅ 找到编辑器: {selector}")
                    break
            except:
                continue
        
        if not editor:
            # 尝试在iframe中查找
            print("⚠️  尝试在iframe中查找编辑器...")
            for frame in page.context.pages[0].frames:
                for selector in editor_selectors:
                    try:
                        editor = await frame.query_selector(selector)
                        if editor:
                            print(f"   ✅ 在iframe中找到编辑器: {selector}")
                            page = frame
                            break
                    except:
                        continue
                if editor:
                    break
        
        if editor:
            test_content = """这是一篇智能测试文章。

今日头条是中国领先的个性化信息聚合平台。
自动化发布可以提高效率。

本次测试验证完整的发布流程。
希望成功！
"""
            try:
                await editor.fill(test_content)
                print(f"✅ 内容填写成功，长度: {len(test_content)} 字")
            except Exception as e:
                print(f"⚠️  fill()失败，尝试click+type: {e}")
                await editor.click()
                await page.keyboard.type(test_content)
                print(f"✅ 使用keyboard.type填写内容")
        else:
            print("❌ 未找到编辑器")
            return
        
        await asyncio.sleep(2)
        
        # 步骤 5: 查找发布按钮
        print("\n[步骤 5] 查找发布按钮...")
        
        button_selectors = [
            'button:has-text("发布")',
            'button.publish-btn',
            '.byte-btn:has-text("发布")',
            'a:has-text("发布")',
            'button[type="submit"]'
        ]
        
        publish_btn = None
        for selector in button_selectors:
            try:
                publish_btn = await page.query_selector(selector)
                if publish_btn and await publish_btn.is_visible():
                    print(f"✅ 找到发布按钮: {selector}")
                    break
            except:
                continue
        
        if publish_btn:
            print("\n[步骤 6] 点击发布...")
            await publish_btn.click()
            print("✅ 已点击发布按钮")
            
            # 等待响应
            print("⏳ 等待发布响应...")
            await asyncio.sleep(10)
            
            # 检查是否有成功提示
            success_indicators = [
                'text=发布成功',
                'text=发表成功',
                '.ant-message-success'
            ]
            
            success_found = False
            for indicator in success_indicators:
                try:
                    elem = await page.query_selector(indicator)
                    if elem and await elem.is_visible():
                        text = await elem.text_content()
                        print(f"✅ 检测到成功提示: {text}")
                        success_found = True
                        break
                except:
                    continue
            
            if success_found:
                print("\n🎉 发布成功！")
            else:
                print("\n⚠️  未检测到明确的成功提示")
                print(f"   当前URL: {page.url}")
                
                # 截图
                screenshot = f"logs/smart_test_after_publish_{int(asyncio.get_event_loop().time())}.png"
                await page.screenshot(path=screenshot, full_page=True)
                print(f"   截图已保存: {screenshot}")
        else:
            print("❌ 未找到发布按钮")
            
            # 列出所有按钮
            buttons = await page.query_selector_all('button, a[class*="btn"]')
            print(f"   页面上有 {len(buttons)} 个按钮")
            for i, btn in enumerate(buttons[:10]):
                text = await btn.text_content()
                print(f"     [{i}] {text.strip()[:30]}")
        
        print("\n⏸️  浏览器保持打开，请检查结果")
        print("   按回车关闭...")
        input()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏸️  按回车关闭...")
        input()
    finally:
        await browser.close()
        await playwright.stop()
        print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(smart_publish_test())
