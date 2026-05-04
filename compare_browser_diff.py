"""
对比 Playwright 和手动打开 Edge 的区别
"""
import asyncio
from playwright.async_api import async_playwright


async def compare_browsers():
    """对比两种方式的差异"""
    
    print("="*80)
    print("对比 Playwright 和手动打开 Edge 的区别")
    print("="*80)
    
    async with async_playwright() as p:
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
        # 启动 Playwright 浏览器
        print("\n[1] 启动 Playwright 浏览器...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./edge_profile_toutiao",
            headless=False,
            executable_path=edge_path,
            viewport={"width": 1920, "height": 1080},
            args=['--start-maximized']
        )
        
        page = await browser.new_page()
        
        # 访问头条发布页面
        print("\n[2] 访问头条发布页面...")
        await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until='domcontentloaded')
        await asyncio.sleep(10)
        
        # 收集诊断信息
        print("\n" + "="*80)
        print("Playwright 浏览器诊断信息：")
        print("="*80)
        
        # 1. User-Agent
        ua = await page.evaluate("() => navigator.userAgent")
        print(f"\nUser-Agent: {ua}")
        
        # 2. Webdriver
        webdriver = await page.evaluate("() => navigator.webdriver")
        print(f"navigator.webdriver: {webdriver}")
        
        # 3. Chrome 对象
        has_chrome = await page.evaluate("() => typeof window.chrome !== 'undefined'")
        print(f"window.chrome: {has_chrome}")
        
        # 4. 屏幕信息
        screen_info = await page.evaluate("""
            () => ({
                width: window.screen.width,
                height: window.screen.height,
                availWidth: window.screen.availWidth,
                availHeight: window.screen.availHeight,
                colorDepth: window.screen.colorDepth,
                pixelDepth: window.screen.pixelDepth
            })
        """)
        print(f"\n屏幕信息: {screen_info}")
        
        # 5. 窗口信息
        window_info = await page.evaluate("""
            () => ({
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
                outerWidth: window.outerWidth,
                outerHeight: window.outerHeight,
                devicePixelRatio: window.devicePixelRatio
            })
        """)
        print(f"窗口信息: {window_info}")
        
        # 6. 插件信息
        plugins = await page.evaluate("() => navigator.plugins.length")
        print(f"\n插件数量: {plugins}")
        
        # 7. 语言
        language = await page.evaluate("() => navigator.language")
        print(f"语言: {language}")
        
        # 8. 时区
        timezone = await page.evaluate("() => Intl.DateTimeFormat().resolvedOptions().timeZone")
        print(f"时区: {timezone}")
        
        # 9. 微前端框架
        garfish_info = await page.evaluate("""
            () => ({
                exists: typeof window.Garfish !== 'undefined',
                apps: window.Garfish ? Object.keys(window.Garfish.apps || {}) : [],
                version: window.Garfish ? window.Garfish.version : 'N/A'
            })
        """)
        print(f"\n微前端框架: {garfish_info}")
        
        # 10. 页面中的 iframe
        iframes = await page.query_selector_all('iframe')
        print(f"\niframe 数量: {len(iframes)}")
        
        # 11. 编辑器状态
        editor_info = await page.evaluate("""
            () => {
                const editor = document.querySelector('div[contenteditable="true"]');
                if (!editor) return { exists: false };
                
                const style = window.getComputedStyle(editor);
                const rect = editor.getBoundingClientRect();
                
                return {
                    exists: true,
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    width: rect.width,
                    height: rect.height,
                    top: rect.top,
                    left: rect.left,
                    inViewport: rect.top >= 0 && rect.left >= 0
                };
            }
        """)
        print(f"编辑器状态: {editor_info}")
        
        # 12. 控制台错误
        print("\n" + "="*80)
        print("请在手动打开的Edge浏览器中（F12控制台）运行以下代码，")
        print("然后告诉我结果，我来对比：")
        print("="*80)
        
        comparison_code = """
// 复制这段代码到手动打开的Edge浏览器控制台中运行
console.log("=== 手动打开的Edge诊断 ===");
console.log("User-Agent:", navigator.userAgent);
console.log("webdriver:", navigator.webdriver);
console.log("window.chrome:", typeof window.chrome);
console.log("屏幕:", window.screen.width, "x", window.screen.height);
console.log("窗口:", window.innerWidth, "x", window.innerHeight);
console.log("插件数量:", navigator.plugins.length);
console.log("语言:", navigator.language);
console.log("时区:", Intl.DateTimeFormat().resolvedOptions().timeZone);
console.log("Garfish:", typeof window.Garfish, window.Garfish ? Object.keys(window.Garfish.apps) : []);

const editor = document.querySelector('div[contenteditable="true"]');
if (editor) {
    const rect = editor.getBoundingClientRect();
    console.log("编辑器位置:", { top: rect.top, left: rect.left, inViewport: rect.top >= 0 });
} else {
    console.log("编辑器: 不存在");
}
"""
        print(comparison_code)
        
        print("\n" + "="*80)
        print("\n操作步骤：")
        print("1. 保持这个 Playwright 浏览器打开")
        print("2. 手动打开一个新的 Edge 浏览器")
        print("3. 访问: https://mp.toutiao.com/profile_v4/graphic/publish")
        print("4. 按 F12 打开开发者工具")
        print("5. 粘贴上面的代码到控制台并运行")
        print("6. 对比两边的输出，告诉我差异")
        print("\n" + "="*80)
        print("\n按回车关闭浏览器...")
        input()
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(compare_browsers())
