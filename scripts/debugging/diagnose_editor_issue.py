"""
诊断并修复头条发布页面编辑区加载问题
"""
import asyncio
from playwright.async_api import async_playwright


async def diagnose_editor_issue():
    """诊断编辑区问题"""
    
    async with async_playwright() as p:
        # 使用 Edge 浏览器
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./edge_profile_toutiao",
            headless=False,
            executable_path=edge_path,
            viewport={"width": 1920, "height": 1080},
            args=['--start-maximized']
        )
        
        page = await browser.new_page()
        
        # 访问发布页面
        print("正在打开发布页面...")
        await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until='domcontentloaded')
        await asyncio.sleep(10)
        
        print("\n" + "="*80)
        print("诊断信息：")
        print("="*80)
        
        # 1. 检查页面中的所有 iframe
        print("\n[1] 检查 iframe：")
        iframes = await page.query_selector_all('iframe')
        print(f"  找到 {len(iframes)} 个 iframe")
        for i, iframe in enumerate(iframes):
            src = await iframe.get_attribute('src')
            print(f"  iframe[{i}]: {src[:100] if src else 'no src'}")
        
        # 2. 检查微前端容器
        print("\n[2] 检查微前端容器：")
        mf_containers = await page.query_selector_all('[class*="garfish"], [class*="micro"], [id*="app"]')
        print(f"  找到 {len(mf_containers)} 个微前端容器")
        for i, container in enumerate(mf_containers[:5]):
            cls = await container.get_attribute('class')
            print(f"  container[{i}]: {cls[:100] if cls else 'no class'}")
        
        # 3. 检查编辑区是否存在
        print("\n[3] 检查编辑区元素：")
        editors = await page.query_selector_all('div[contenteditable="true"]')
        print(f"  找到 {len(editors)} 个可编辑 div")
        
        title_inputs = await page.query_selector_all('input[placeholder*="标题"], textarea[placeholder*="标题"]')
        print(f"  找到 {len(title_inputs)} 个标题输入框")
        
        # 4. 执行 JavaScript 诊断
        print("\n[4] 执行 JavaScript 诊断：")
        diagnosis = await page.evaluate("""
            () => {
                const result = {
                    // 检查 Garfish 微前端框架
                    garfish: typeof window.Garfish !== 'undefined',
                    garfishApps: window.Garfish ? Object.keys(window.Garfish.apps || {}) : [],
                    
                    // 检查页面高度
                    bodyScrollHeight: document.body.scrollHeight,
                    bodyClientHeight: document.body.clientHeight,
                    windowInnerHeight: window.innerHeight,
                    
                    // 检查关键元素
                    hasEditor: !!document.querySelector('div[contenteditable="true"]'),
                    hasTitleInput: !!document.querySelector('input[placeholder*="标题"]'),
                    hasFooter: !!document.querySelector('.garr-footer, [class*="footer"]'),
                    
                    // 检查 CSS 类
                    bodyClasses: document.body.className,
                    
                    // 检查是否有错误
                    errors: [],
                };
                
                // 检查控制台错误
                if (window.__playwright_errors__) {
                    result.errors = window.__playwright_errors__;
                }
                
                return result;
            }
        """)
        
        print(f"  Garfish 框架: {diagnosis['garfish']}")
        print(f"  Garfish 应用: {diagnosis['garfishApps']}")
        print(f"  页面高度: {diagnosis['bodyScrollHeight']}px")
        print(f"  窗口高度: {diagnosis['windowInnerHeight']}px")
        print(f"  有编辑器: {diagnosis['hasEditor']}")
        print(f"  有标题输入: {diagnosis['hasTitleInput']}")
        print(f"  有底部栏: {diagnosis['hasFooter']}")
        
        # 5. 尝试手动触发编辑区加载
        print("\n[5] 尝试手动触发编辑区加载...")
        print("  请查看浏览器，我会尝试以下操作：")
        print("  - 调整窗口大小")
        print("  - 滚动页面")
        print("  - 点击编辑区域")
        
        await asyncio.sleep(2)
        
        # 调整窗口大小触发重新渲染
        await page.set_viewport_size({"width": 1921, "height": 1080})
        await asyncio.sleep(2)
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await asyncio.sleep(2)
        
        print("\n  窗口大小已调整，请检查编辑区是否出现！")
        print("\n" + "="*80)
        print("请在浏览器中检查：")
        print("  1. 左侧编辑区是否出现？")
        print("  2. 标题输入框是否可见？")
        print("  3. 正文编辑器是否可见？")
        print("\n按回车继续...")
        input()
        
        # 6. 尝试点击可能的编辑区容器
        print("\n[6] 尝试点击编辑区容器...")
        await page.evaluate("""
            () => {
                // 查找所有可能的容器并点击
                const containers = document.querySelectorAll('.graphic-editor, .editor-container, .publish-editor, [class*="editor"]');
                containers.forEach(el => {
                    console.log('Found container:', el.className);
                    el.click();
                });
            }
        """)
        await asyncio.sleep(3)
        
        print("\n" + "="*80)
        print("最终检查：")
        print("  编辑区是否出现？")
        print("  如果没有，请截图告诉我看到了什么")
        print("\n按回车关闭浏览器...")
        input()
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(diagnose_editor_issue())
