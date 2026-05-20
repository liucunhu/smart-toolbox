"""
测试通过工具栏插入图片 - 使用更广泛的选择器
"""
import asyncio
from playwright.async_api import async_playwright
import os


async def test_insert_image():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(5)
        
        # 先填写一些文本
        print("填写测试文本...")
        await page.fill('div[contenteditable="true"]', "这是测试文章内容。\n\n第二段内容。\n\n第三段内容。")
        await asyncio.sleep(2)
        
        print("=" * 80)
        print("测试插入图片到文章")
        print("=" * 80)
        
        # 方法1：查找所有 syl-toolbar-button 按钮并尝试点击
        print("\n【方法1】遍历所有工具栏按钮...")
        
        buttons_info = await page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('.syl-toolbar-button');
                const results = [];
                
                for (let i = 0; i < buttons.length; i++) {
                    const btn = buttons[i];
                    const rect = btn.getBoundingClientRect();
                    
                    // 只考虑编辑器上方的工具栏按钮
                    if (rect.width > 0 && rect.top > 100 && rect.top < 350) {
                        results.push({
                            index: i,
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                            width: rect.width,
                            height: rect.height,
                            hasListIcon: btn.querySelector('.list-icon-wrapper') !== null,
                            hasEmojiIcon: btn.querySelector('.emoji-icon-wrapper') !== null
                        });
                    }
                }
                
                return results;
            }
        """)
        
        print(f"找到 {len(buttons_info)} 个工具栏按钮")
        
        # 准备测试图片
        test_image = os.path.abspath('uploads/article_images/article_img_e8c61185.jpg')
        if not os.path.exists(test_image):
            print(f"⚠️  测试图片不存在: {test_image}")
            # 使用封面图
            test_image = os.path.abspath('uploads/llm_covers/llm_cover_1777835411_1779.jpg')
        
        print(f"测试图片: {test_image}")
        
        # 尝试点击第4个按钮（通常是图片按钮）
        if len(buttons_info) >= 4:
            target_btn = buttons_info[3]  # 第4个按钮（索引3）
            print(f"\n尝试点击第4个按钮 (位置: {target_btn['x']}, {target_btn['y']})...")
            
            await page.mouse.click(target_btn['x'], target_btn['y'])
            await asyncio.sleep(2)
            
            # 检查是否出现文件选择器或图片对话框
            file_inputs = await page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input[type="file"]');
                    return inputs.length;
                }
            """)
            
            print(f"文件选择器数量: {file_inputs}")
            
            if file_inputs > 0:
                print("✅ 找到文件选择器，上传图片...")
                try:
                    file_input = page.locator('input[type="file"]').first
                    await file_input.set_input_files(test_image)
                    print("✅ 图片已上传")
                    await asyncio.sleep(3)
                    
                    # 截图验证
                    await page.screenshot(path='logs/image_insert_test.png', full_page=True)
                    print("✅ 截图已保存: logs/image_insert_test.png")
                except Exception as e:
                    print(f"❌ 上传失败: {e}")
            else:
                print("❌ 未找到文件选择器")
                await page.screenshot(path='logs/after_button_click.png', full_page=True)
                print("截图已保存: logs/after_button_click.png")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_insert_image())
