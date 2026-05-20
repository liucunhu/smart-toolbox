"""
查找头条编辑器工具栏中的图片按钮
"""
import asyncio
from playwright.async_api import async_playwright


async def find_image_button():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(5)
        
        print("=" * 80)
        print("查找头条编辑器工具栏图片按钮")
        print("=" * 80)
        
        # 1. 查找所有工具栏相关元素
        print("\n【步骤1】查找所有可能的工具栏元素...")
        toolbar_info = await page.evaluate("""
            () => {
                const results = [];
                
                // 查找所有包含图标的元素（包括其父元素）
                const icons = document.querySelectorAll('i, svg, [class*="icon"], [class*="Icon"]');
                for (const icon of icons) {
                    const rect = icon.getBoundingClientRect();
                    if (rect.width > 0 && rect.top > 100 && rect.top < 400) {
                        // 获取父元素信息
                        const parent = icon.parentElement;
                        results.push({
                            tag: icon.tagName,
                            className: icon.className || '',
                            parentTag: parent ? parent.tagName : '',
                            parentClass: parent ? (parent.className || '') : '',
                            title: icon.getAttribute('title') || '',
                            ariaLabel: icon.getAttribute('aria-label') || '',
                            parentTitle: parent ? (parent.getAttribute('title') || '') : '',
                            rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                        });
                    }
                }
                
                return results.slice(0, 30);
            }
        """)
        
        print(f"找到 {len(toolbar_info)} 个图标元素:")
        for i, item in enumerate(toolbar_info):
            class_name = item.get('className', '')
            parent_class = item.get('parentClass', '')
            title = item.get('title', '')
            parent_title = item.get('parentTitle', '')
            aria_label = item.get('ariaLabel', '')
            
            print(f"  {i+1}. {item['tag']} -> {item['parentTag']}")
            if class_name:
                print(f"      class: {class_name[:50]}")
            if parent_class:
                print(f"      parent-class: {parent_class[:50]}")
            if title:
                print(f"      title: {title}")
            if parent_title:
                print(f"      parent-title: {parent_title}")
            if aria_label:
                print(f"      aria-label: {aria_label}")
        
        # 2. 查找所有按钮（包括它们的子元素）
        print("\n【步骤2】查找所有按钮及其子元素...")
        buttons_info = await page.evaluate("""
            () => {
                const results = [];
                const buttons = document.querySelectorAll('button, [role="button"]');
                
                for (const btn of buttons) {
                    const rect = btn.getBoundingClientRect();
                    if (rect.width > 0 && rect.top > 100 && rect.top < 400) {
                        const text = (btn.textContent || '').trim().substring(0, 30);
                        
                        // 查找按钮内的svg或icon
                        const svg = btn.querySelector('svg');
                        const icon = btn.querySelector('i, [class*="icon"]');
                        
                        results.push({
                            tag: btn.tagName,
                            text: text,
                            className: btn.className || '',
                            title: btn.getAttribute('title') || '',
                            hasSvg: !!svg,
                            hasIcon: !!icon,
                            svgClass: svg ? (svg.className || '') : '',
                            iconClass: icon ? (icon.className || '') : '',
                            childCount: btn.children.length,
                            rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                        });
                    }
                }
                
                return results.slice(0, 30);
            }
        """)
        
        print(f"找到 {len(buttons_info)} 个按钮:")
        for i, item in enumerate(buttons_info):
            text = item.get('text', '')
            class_name = item.get('className', '')
            title = item.get('title', '')
            has_svg = item.get('hasSvg', False)
            has_icon = item.get('hasIcon', False)
            
            print(f"  {i+1}. {item['tag']} - text: '{text}' children: {item['childCount']}")
            if title:
                print(f"      title: {title}")
            if class_name:
                print(f"      class: {class_name[:60]}")
            if has_svg:
                svg_class = item.get('svgClass', '')
                print(f"      ✅ 有SVG: {svg_class[:40] if svg_class else 'N/A'}")
            if has_icon:
                icon_class = item.get('iconClass', '')
                print(f"      ✅ 有Icon: {icon_class[:40] if icon_class else 'N/A'}")
        
        # 3. 查找工具栏容器
        print("\n【步骤3】查找工具栏容器...")
        toolbar_containers = await page.evaluate("""
            () => {
                const containers = [];
                
                // 查找常见的工具栏类名
                const selectors = [
                    '[class*="toolbar"]',
                    '[class*="Toolbar"]',
                    '[class*="editor-toolbar"]',
                    '[class*="format-bar"]',
                    '[class*="menu"]'
                ];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 100 && rect.top > 100 && rect.top < 400) {
                            containers.push({
                                selector: selector,
                                className: el.className,
                                childrenCount: el.children.length,
                                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                            });
                        }
                    }
                }
                
                return containers;
            }
        """)
        
        print(f"找到 {len(toolbar_containers)} 个工具栏容器:")
        for i, container in enumerate(toolbar_containers):
            class_name = container.get('className', '')
            print(f"  {i+1}. {container['selector']}")
            print(f"      class: {class_name[:80] if class_name else 'N/A'}")
            print(f"      子元素数: {container['childrenCount']}")
        
        # 4. 截图保存
        await page.screenshot(path='logs/toolbar_debug.png', full_page=True)
        print("\n✅ 截图已保存: logs/toolbar_debug.png")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(find_image_button())
