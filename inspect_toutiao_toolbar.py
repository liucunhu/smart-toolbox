"""
查看头条发布页面的工具栏结构
"""
import asyncio
from playwright.async_api import async_playwright


async def inspect_toutiao_toolbar():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    
    # 导航到发布页面
    await page.goto('https://mp.toutiao.com/profile_v4/graphic/publish')
    await asyncio.sleep(3)
    
    # 获取工具栏HTML
    toolbar_html = await page.evaluate("""
        () => {
            // 查找工具栏
            const toolbar = document.querySelector('.toolbar') || 
                           document.querySelector('[class*="toolbar"]') ||
                           document.querySelector('[class*="editor-toolbar"]');
            
            if (!toolbar) return '未找到工具栏';
            
            return toolbar.outerHTML;
        }
    """)
    
    print("=" * 80)
    print("工具栏 HTML:")
    print("=" * 80)
    print(toolbar_html[:2000])  # 只打印前2000字符
    
    # 获取所有按钮并查找图片按钮
    buttons_info = await page.evaluate("""
        () => {
            const toolbar = document.querySelector('.syl-editor-toolbar') || 
                           document.querySelector('.syl-toolbar');
            if (!toolbar) return [];
            
            const buttons = toolbar.querySelectorAll('.syl-toolbar-button');
            return Array.from(buttons).map((btn, idx) => ({
                index: idx,
                text: btn.textContent?.trim(),
                title: btn.getAttribute('title'),
                ariaLabel: btn.getAttribute('aria-label'),
                className: btn.className,
                parentClass: btn.parentElement?.className,
                hasSvg: btn.querySelector('svg') !== null,
                svgPath: btn.querySelector('svg')?.innerHTML?.substring(0, 150),
                allClasses: btn.className + ' ' + (btn.parentElement?.className || '')
            }));
        }
    """)
    
    print("\n" + "=" * 80)
    print("工具栏按钮详细信息（查找图片按钮）:")
    print("=" * 80)
    for btn in buttons_info:
        print(f"\n按钮 #{btn['index']}:")
        print(f"  类名: {btn['parentClass']}")
        print(f"  SVG内容: {btn['svgPath'][:100]}")
        
        # 标记可能是图片按钮的
        if 'image' in btn['allClasses'].lower() or 'photo' in btn['allClasses'].lower() or 'picture' in btn['allClasses'].lower():
            print(f"  >>> 可能是图片按钮！ <<<")
    
    # 尝试点击图片按钮（按钮 #14，可能是图片/相册图标）
    print("\n" + "=" * 80)
    print("尝试点击图片按钮并监控变化...")
    print("=" * 80)
    
    # 监听网络请求
    page.on('request', lambda req: print(f"  网络请求: {req.url[:80]}"))
    
    # 点击图片按钮
    image_button = await page.query_selector('.syl-toolbar-button:nth-child(15)')  # 第15个（索引14）
    if image_button:
        print("找到图片按钮，点击...")
        await image_button.click()
        await asyncio.sleep(3)
        
        # 检查是否有对话框出现
        dialogs = await page.evaluate("""
            () => {
                const modals = document.querySelectorAll('.byte-modal, .modal, [role="dialog"], .syl-image-modal, [class*="image-upload"]');
                return Array.from(modals).map(m => ({
                    className: m.className,
                    visible: m.offsetParent !== null,
                    text: m.textContent?.substring(0, 100)
                }));
            }
        """)
        
        print(f"\n找到 {len(dialogs)} 个对话框:")
        for d in dialogs:
            print(f"  - {d['className']}: {d['text'][:50]}")
        
        # 检查是否有文件输入框
        file_inputs = await page.query_selector_all('input[type="file"]')
        print(f"\n找到 {len(file_inputs)} 个文件输入框")
        
        # 截图
        await page.screenshot(path='logs/after_click_image_button.png', full_page=True)
        print("已保存截图: logs/after_click_image_button.png")
    else:
        print("未找到图片按钮")
    
    await playwright.stop()


if __name__ == '__main__':
    asyncio.run(inspect_toutiao_toolbar())
