"""
今日头条发布流程详细调试脚本
逐步检查每个操作是否成功
"""
import asyncio
import json
from playwright.async_api import async_playwright
from app.utils.logger import logger


async def debug_toutiao_publish():
    """调试头条发布流程"""
    
    print("="*80)
    print("🔍 今日头条发布流程调试")
    print("="*80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = await context.new_page()
    
    try:
        # ========== 步骤 1: 登录 ==========
        print("\n[步骤 1/7] 打开头条创作者平台...")
        await page.goto("https://mp.toutiao.com/", timeout=30000)
        await asyncio.sleep(3)
        print(f"✅ 当前URL: {page.url}")
        
        # 检查是否已登录
        if "login" in page.url or "sso" in page.url:
            print("⚠️  未登录，需要手动登录")
            print("请在浏览器中完成登录，然后按回车继续...")
            input()
        else:
            print("✅ 已登录状态")
        
        # ========== 步骤 2: 进入发布页面 ==========
        print("\n[步骤 2/7] 进入文章发布页面...")
        await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", timeout=30000)
        await asyncio.sleep(5)
        print(f"✅ 当前URL: {page.url}")
        
        # 截图
        screenshot_path = "logs/debug_step2_publish_page.png"
        await page.screenshot(path=screenshot_path)
        print(f"📸 截图已保存: {screenshot_path}")
        
        # ========== 步骤 3: 检查并填写标题 ==========
        print("\n[步骤 3/7] 查找标题输入框...")
        title_selectors = [
            'input[placeholder="请输入标题"]',
            'textarea[placeholder*="标题"]',
            'input[name="title"]'
        ]
        
        title_input = None
        for selector in title_selectors:
            title_input = await page.query_selector(selector)
            if title_input:
                print(f"✅ 找到标题输入框: {selector}")
                break
        
        if title_input:
            test_title = f"测试文章_{asyncio.get_event_loop().time()}"
            await title_input.fill(test_title)
            await asyncio.sleep(1)
            
            # 验证是否填写成功
            filled_value = await title_input.input_value()
            if filled_value == test_title:
                print(f"✅ 标题填写成功: {test_title}")
            else:
                print(f"❌ 标题填写失败！期望: {test_title}, 实际: {filled_value}")
        else:
            print("❌ 未找到标题输入框！")
            print("可用的输入框:")
            all_inputs = await page.query_selector_all('input, textarea')
            for i, inp in enumerate(all_inputs[:10]):
                placeholder = await inp.get_attribute('placeholder')
                name = await inp.get_attribute('name')
                print(f"  [{i}] placeholder={placeholder}, name={name}")
        
        # ========== 步骤 4: 检查并填写内容 ==========
        print("\n[步骤 4/7] 查找内容编辑器...")
        editor_selectors = [
            'div[contenteditable="true"]',
            'div.toutiao-editor',
            'div[class*="editor"]',
            'iframe'
        ]
        
        editor = None
        for selector in editor_selectors:
            editor = await page.query_selector(selector)
            if editor:
                print(f"✅ 找到编辑器: {selector}")
                break
        
        if editor:
            test_content = "这是测试内容，用于验证发布流程是否正常。"
            
            # 尝试不同的填写方式
            try:
                # 方式1: 直接fill
                await editor.fill(test_content)
                print("✅ 使用 fill() 填写内容")
            except Exception as e:
                print(f"⚠️  fill() 失败: {e}")
                try:
                    # 方式2: 点击后输入
                    await editor.click()
                    await page.keyboard.type(test_content)
                    print("✅ 使用 click() + keyboard.type() 填写内容")
                except Exception as e2:
                    print(f"❌ 所有内容填写方式都失败: {e2}")
            
            await asyncio.sleep(2)
            
            # 验证内容
            content_text = await editor.text_content()
            if test_content in content_text:
                print(f"✅ 内容填写成功")
            else:
                print(f"⚠️  内容可能未正确填写")
                print(f"   编辑器内容: {content_text[:100]}...")
        else:
            print("❌ 未找到内容编辑器！")
            print("页面上所有的 div:")
            all_divs = await page.query_selector_all('div')
            for i, div in enumerate(all_divs[:20]):
                class_name = await div.get_attribute('class')
                if class_name and ('edit' in class_name.lower() or 'content' in class_name.lower()):
                    print(f"  [{i}] class={class_name}")
        
        # ========== 步骤 5: 检查分类选择 ==========
        print("\n[步骤 5/7] 查找分类选择器...")
        category_selectors = [
            'select',
            'div[class*="category"]',
            'div[class*="classify"]',
            'span:has-text("分类")'
        ]
        
        category_found = False
        for selector in category_selectors:
            elem = await page.query_selector(selector)
            if elem:
                print(f"✅ 找到分类元素: {selector}")
                category_found = True
                break
        
        if not category_found:
            print("⚠️  未找到分类选择器（可能不需要）")
        
        # ========== 步骤 6: 检查标签输入 ==========
        print("\n[步骤 6/7] 查找标签输入框...")
        tag_selectors = [
            'input[placeholder*="标签"]',
            'input[name*="tag"]',
            'div[class*="tag"] input'
        ]
        
        tag_found = False
        for selector in tag_selectors:
            elem = await page.query_selector(selector)
            if elem:
                print(f"✅ 找到标签输入框: {selector}")
                tag_found = True
                break
        
        if not tag_found:
            print("⚠️  未找到标签输入框（可能不需要）")
        
        # ========== 步骤 7: 查找发布按钮 ==========
        print("\n[步骤 7/7] 查找发布按钮...")
        button_selectors = [
            'button:has-text("发布")',
            'button.publish-btn',
            'button[class*="publish"]',
            'button[type="submit"]'
        ]
        
        publish_button = None
        for selector in button_selectors:
            try:
                publish_button = await page.query_selector(selector)
                if publish_button:
                    is_visible = await publish_button.is_visible()
                    is_enabled = await publish_button.is_enabled()
                    print(f"✅ 找到发布按钮: {selector}")
                    print(f"   可见: {is_visible}, 可用: {is_enabled}")
                    
                    button_text = await publish_button.text_content()
                    print(f"   按钮文本: {button_text}")
                    break
            except Exception as e:
                continue
        
        if not publish_button:
            print("❌ 未找到发布按钮！")
            print("页面上所有的 button:")
            all_buttons = await page.query_selector_all('button')
            for i, btn in enumerate(all_buttons):
                text = await btn.text_content()
                class_name = await btn.get_attribute('class')
                print(f"  [{i}] text='{text}', class={class_name}")
        
        # ========== 最终截图 ==========
        final_screenshot = "logs/debug_final_state.png"
        await page.screenshot(path=final_screenshot, full_page=True)
        print(f"\n📸 最终状态截图: {final_screenshot}")
        
        # ========== 总结 ==========
        print("\n" + "="*80)
        print("📊 调试总结")
        print("="*80)
        print(f"标题输入框: {'✅ 找到' if title_input else '❌ 未找到'}")
        print(f"内容编辑器: {'✅ 找到' if editor else '❌ 未找到'}")
        print(f"发布按钮: {'✅ 找到' if publish_button else '❌ 未找到'}")
        print(f"\n💡 下一步:")
        print(f"   1. 查看截图: logs/debug_step2_publish_page.png")
        print(f"   2. 查看截图: logs/debug_final_state.png")
        print(f"   3. 根据截图分析页面结构")
        print(f"   4. 更新选择器以匹配实际页面")
        print("="*80)
        
        print("\n⏸️  浏览器将保持打开，请检查页面状态")
        print("   确认无误后，在此终端按回车关闭浏览器...")
        input()
        
    except Exception as e:
        print(f"\n❌ 调试过程出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 出错时也截图
        try:
            error_screenshot = "logs/debug_error_state.png"
            await page.screenshot(path=error_screenshot)
            print(f"📸 错误状态截图: {error_screenshot}")
        except:
            pass
        
        print("\n⏸️  按回车关闭浏览器...")
        input()
    finally:
        await browser.close()
        await playwright.stop()
        print("\n✅ 调试完成")


if __name__ == "__main__":
    asyncio.run(debug_toutiao_publish())
