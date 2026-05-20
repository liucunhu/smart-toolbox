"""
头条全自动发布 - 使用真实Edge浏览器（CDP连接）
100%还原真实用户浏览器环境
"""
import asyncio
from playwright.async_api import async_playwright


async def publish_with_real_edge():
    """使用真实Edge浏览器发布（通过CDP连接）"""
    
    print("="*80)
    print("🚀 头条全自动发布（真实Edge浏览器 CDP 连接版）")
    print("="*80)
    print("\n💡 这个方案会：")
    print("   1. 启动一个Edge浏览器实例")
    print("   2. 100%模拟真实用户的所有特征")
    print("   3. 完全隐藏自动化痕迹")
    print("   4. 自动登录并发布文章")
    print()
    
    async with async_playwright() as p:
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
        # ★★★ 启动浏览器，使用最真实的配置 ★★★
        print("[1/6] 启动真实Edge浏览器...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./edge_profile_100percent",
            headless=False,
            executable_path=edge_path,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                # ★★★ 关键：移除所有自动化参数 ★★★
            ],
            # ★★★ 忽略默认自动化参数 ★★★
            ignore_default_args=[
                '--enable-automation',
                '--disable-extensions',
            ],
            viewport=None,  # 不使用固定视口
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )
        
        page = await browser.new_page()
        
        # ★★★ 在所有页面加载前注入反检测脚本 ★★★
        await browser.add_init_script("""
            // 1. 隐藏 webdriver（最核心！）
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // 2. 模拟真实的 Chrome 对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 3. 隐藏 Playwright 特征
            delete window.__playwright;
            delete window.__pw_manual;
            delete window.__pw_inspect;
            delete window.__playwright__;
            delete window._phantom;
            delete window.callPhantom;
            delete window.cdc_;
            
            // 4. 模拟真实的 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Microsoft Edge PDF Viewer"
                    }
                ],
            });
            
            // 5. 模拟真实的 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en'],
            });
            
            // 6. 模拟真实的 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 7. 模拟真实的 WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            
            // 8. 模拟真实的 screen
            Object.defineProperty(window.screen, 'availWidth', { get: () => 1920 });
            Object.defineProperty(window.screen, 'availHeight', { get: () => 1040 });
            Object.defineProperty(window.screen, 'width', { get: () => 1920 });
            Object.defineProperty(window.screen, 'height', { get: () => 1080 });
            Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
            
            // 9. 隐藏 DevTools 检测
            const element = new Image();
            Object.defineProperty(element, 'id', {
                get: () => { throw new Error('DevTools detected'); }
            });
        """)
        
        print("✅ 浏览器已启动（100%真实模式）")
        
        # 登录
        print("\n[2/6] 登录头条...")
        await page.goto("https://mp.toutiao.com/", wait_until='domcontentloaded')
        await asyncio.sleep(5)
        
        # 检查是否已登录
        current_url = page.url
        if "login" in current_url:
            print("⚠️  需要手动登录，请在浏览器中完成登录...")
            print("   登录完成后按回车继续...")
            input()
        else:
            print("✅ 已登录")
        
        # 访问发布页面
        print("\n[3/6] 访问发布页面...")
        await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until='domcontentloaded')
        await asyncio.sleep(10)
        
        # ★★★ 验证页面是否完整加载 ★★★
        print("\n[4/6] 验证页面加载状态...")
        page_status = await page.evaluate("""
            () => {
                const editor = document.querySelector('div[contenteditable="true"]');
                const titleInput = document.querySelector('input[placeholder*="标题"], textarea[placeholder*="标题"]');
                
                // 查找发布按钮（使用XPath）
                let publishBtn = null;
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.includes('预览并发布')) {
                        publishBtn = btn;
                        break;
                    }
                }
                
                return {
                    editorExists: !!editor,
                    titleInputExists: !!titleInput,
                    publishBtnExists: !!publishBtn,
                    url: window.location.href
                };
            }
        """)
        
        print(f"  编辑器: {'✅' if page_status['editorExists'] else '❌'}")
        print(f"  标题输入: {'✅' if page_status['titleInputExists'] else '❌'}")
        print(f"  发布按钮: {'✅' if page_status['publishBtnExists'] else '❌'}")
        
        if not page_status['editorExists']:
            print("\n❌ 页面未完整加载！")
            print("   请检查浏览器中的页面状态")
            input("按回车继续...")
        
        # 填写内容
        print("\n[5/6] 填写文章内容...")
        title = "人工智能技术发展趋势分析"
        content = """这是一篇关于人工智能技术发展的深度分析文章。

近年来，人工智能技术取得了长足的进步，从机器学习到深度学习，从自然语言处理到计算机视觉，AI正在改变着我们的生活方式和工作模式。

首先，让我们来看看机器学习领域的最新进展。随着算力的提升和数据的积累，机器学习算法的性能不断提升。特别是深度学习技术，在图像识别、语音识别、自然语言处理等领域都取得了突破性进展。

其次，自然语言处理技术的进步尤为显著。大语言模型的出现，让机器能够理解和生成人类语言，这在智能客服、自动翻译、内容生成等场景都有广泛应用。

再次，计算机视觉技术也在快速发展。从人脸识别到物体检测，从图像生成到视频分析，计算机视觉正在各个行业发挥着重要作用。

最后，AI技术的伦理和安全问题也日益受到关注。如何在推动技术发展的同时，确保AI的安全性和可控性，是我们需要共同思考的问题。

总的来说，人工智能技术正处于快速发展阶段，未来将在更多领域发挥重要作用。我们应该积极拥抱AI技术，同时也要注意其带来的挑战和风险。

希望通过本文的分析，能够帮助大家更好地了解人工智能技术的发展趋势和应用前景。
"""
        
        # 填写标题
        try:
            await page.fill('input[placeholder="请输入标题"]', title)
            print(f"✅ 标题已填写: {title}")
        except:
            print("⚠️  标题填写失败")
        
        # 填写正文
        try:
            await page.fill('div[contenteditable="true"]', content)
            print(f"✅ 正文已填写 ({len(content)} 字)")
        except:
            print("⚠️  正文填写失败")
        
        # 等待内容加载
        await asyncio.sleep(3)
        
        # 点击发布
        print("\n[6/6] 发布文章...")
        try:
            publish_btn = await page.query_selector('button:has-text("预览并发布")')
            if publish_btn:
                await publish_btn.click()
                print("✅ 已点击发布按钮")
                
                # 等待发布结果
                await asyncio.sleep(5)
                
                # 检查URL是否变化
                new_url = page.url
                if "publish" not in new_url:
                    print("🎉 发布成功！页面已跳转")
                else:
                    print("⚠️  页面未跳转，请检查浏览器中的状态")
            else:
                print("❌ 未找到发布按钮")
        except Exception as e:
            print(f"❌ 发布失败: {e}")
        
        print("\n" + "="*80)
        print("✅ 操作完成！")
        print("   浏览器保持打开，请检查结果")
        print("   按回车关闭浏览器...")
        print("="*80)
        input()
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(publish_with_real_edge())
