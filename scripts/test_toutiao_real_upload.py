"""
测试头条的真实上传机制
通过手动在浏览器中操作并抓包，找到真正的API
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def test_real_upload():
    async with async_playwright() as p:
        # 连接真实浏览器
        browser = await p.chromium.connect_over_cdp(
            "http://127.0.0.1:9222"
        )
        
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("=" * 80)
        print("测试头条真实上传机制")
        print("=" * 80)
        
        # 确保在发布页面
        if "publish" not in page.url:
            print("\n跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print(f"\n当前URL: {page.url}")
        
        # 准备测试图片
        test_image_path = os.path.abspath('logs/cover_upload_debug.png')
        if not os.path.exists(test_image_path):
            # 创建一个简单的测试图片
            from PIL import Image
            img = Image.new('RGB', (800, 600), color='red')
            img.save(test_image_path)
            print(f"创建测试图片: {test_image_path}")
        
        print(f"\n测试图片路径: {test_image_path}")
        
        # 监听所有网络请求
        print("\n【设置网络监听】")
        all_requests = []
        
        def handle_request(request):
            if any(keyword in request.url.lower() for keyword in ['upload', 'image', 'cover', 'file']):
                all_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'resource_type': request.resource_type,
                    'post_data': request.post_data
                })
                print(f"   📡 [{request.method}] {request.url[:150]}")
        
        page.on("request", handle_request)
        
        # 方法1：尝试使用CDP协议直接触发文件选择器
        print("\n【方法1】使用CDP协议触发文件选择器...")
        
        try:
            # 获取CDP session
            cdp_session = await page.context.new_cdp_session(page)
            
            # 查找封面区域的DOM节点
            cover_node = await page.evaluate("""
                () => {
                    const containers = document.querySelectorAll('div');
                    for (const div of containers) {
                        const text = (div.textContent || '').trim();
                        if (text.includes('展示封面') && text.length < 100) {
                            return {
                                text: text.substring(0, 50),
                                className: div.className,
                                tagName: div.tagName
                            };
                        }
                    }
                    return null;
                }
            """)
            
            if cover_node:
                print(f"   找到封面区域: {cover_node['text']}")
                
                # 尝试通过CDP模拟真实的用户交互
                print("   尝试模拟鼠标点击...")
                
                # 获取封面区域的位置
                rect = await page.evaluate("""
                    () => {
                        const containers = document.querySelectorAll('div');
                        for (const div of containers) {
                            const text = (div.textContent || '').trim();
                            if (text.includes('展示封面') && text.length < 100) {
                                const r = div.getBoundingClientRect();
                                return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
                            }
                        }
                        return { x: 0, y: 0 };
                    }
                """)
                
                print(f"   封面区域中心位置: ({rect['x']}, {rect['y']})")
                
                # 使用CDP发送鼠标事件
                await cdp_session.send('Input.dispatchMouseEvent', {
                    'type': 'mousePressed',
                    'x': rect['x'],
                    'y': rect['y'],
                    'button': 'left',
                    'clickCount': 1
                })
                
                await asyncio.sleep(0.1)
                
                await cdp_session.send('Input.dispatchMouseEvent', {
                    'type': 'mouseReleased',
                    'x': rect['x'],
                    'y': rect['y'],
                    'button': 'left',
                    'clickCount': 1
                })
                
                print("   ✅ 已发送鼠标点击事件")
                await asyncio.sleep(2)
                
            else:
                print("   ❌ 未找到封面区域")
        
        except Exception as e:
            print(f"   ⚠️ CDP方法失败: {e}")
        
        # 检查是否有网络请求
        if all_requests:
            print(f"\n✅ 捕获到 {len(all_requests)} 个相关请求:")
            for req in all_requests:
                print(f"   - {req['method']} {req['url'][:100]}")
        else:
            print("\n❌ 未捕获到任何上传请求")
            print("   说明：头条可能使用了特殊的上传机制")
        
        # 方法2：尝试注入代码，覆盖头条的上传函数
        print("\n【方法2】尝试拦截头条的上传逻辑...")
        
        interception_result = await page.evaluate("""
            () => {
                // 保存原始的XMLHttpRequest
                const originalXHR = window.XMLHttpRequest;
                const uploads = [];
                
                // 重写XMLHttpRequest
                window.XMLHttpRequest = function() {
                    const xhr = new originalXHR();
                    const originalOpen = xhr.open;
                    const originalSend = xhr.send;
                    
                    xhr.open = function(method, url, ...args) {
                        if (url.includes('upload') || url.includes('image') || url.includes('cover')) {
                            console.log('拦截到上传请求:', method, url);
                            uploads.push({ method, url });
                        }
                        return originalOpen.call(this, method, url, ...args);
                    };
                    
                    xhr.send = function(data) {
                        if (data instanceof FormData) {
                            console.log('FormData内容:', Array.from(data.entries()));
                        }
                        return originalSend.call(this, data);
                    };
                    
                    return xhr;
                };
                
                return {
                    intercepted: true,
                    uploads: uploads
                };
            }
        """)
        
        print(f"   拦截结果: {interception_result}")
        
        # 截图保存
        await page.screenshot(path='logs/upload_attempt_after_click.png', full_page=True)
        print("\n   [OK] 截图已保存: logs/upload_attempt_after_click.png")
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_real_upload())
