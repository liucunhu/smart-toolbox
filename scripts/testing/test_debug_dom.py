"""
调试头条文章列表页面的DOM结构
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_dom_structure():
    """调试DOM结构"""
    print("=" * 80)
    print("调试头条文章列表页面的DOM结构")
    print("=" * 80)
    
    import subprocess
    import os
    import socket
    
    async with async_playwright() as p:
        # 步骤1：检查CDP端口
        print("\n[步骤1] 检查CDP端口9222...")
        cdp_port = 9222
        cdp_available = False
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', cdp_port))
            if result == 0:
                cdp_available = True
                print(f"✅ CDP端口 {cdp_port} 可用")
            sock.close()
        except Exception as e:
            print(f"❌ 检查CDP端口失败: {e}")
        
        # 步骤2：如果CDP不可用，启动Edge浏览器
        if not cdp_available:
            print("\n[步骤2] 启动Edge浏览器（带远程调试）...")
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            if not os.path.exists(edge_path):
                edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            
            if not os.path.exists(edge_path):
                print("❌ 未找到Edge浏览器")
                return
            
            user_data_dir = "./edge_profile_toutiao_analytics"
            cmd = [
                edge_path,
                f'--remote-debugging-port={cdp_port}',
                f'--user-data-dir={user_data_dir}',
                'https://mp.toutiao.com/'
            ]
            
            process = subprocess.Popen(cmd)
            print("✅ Edge浏览器已启动")
            print("   等待浏览器完全启动...")
            await asyncio.sleep(5)
        else:
            print("\n[步骤2] 使用现有的Edge浏览器实例")
        
        # 步骤3：连接CDP
        print("\n[步骤3] 连接CDP...")
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
        
        # 获取context
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
        else:
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )
        
        # 创建新标签页
        print("   创建新标签页...")
        page = await context.new_page()
        print(f"✅ CDP连接成功")
        
        try:
            # 步骤4：访问文章列表页面
            print("\n[步骤4] 访问头条文章列表页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/articles", timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(8)
            
            # 截图
            await page.screenshot(path="logs/debug_dom.png", full_page=True)
            print("✅ 已截图: logs/debug_dom.png")
            
            # 获取页面标题
            title = await page.title()
            print(f"\n[步骤5] 页面标题: {title}")
            
            # 使用更宽松的等待策略
            print("   等待页面元素加载...")
            try:
                await page.wait_for_load_state('domcontentloaded', timeout=5000)
            except:
                pass
            await asyncio.sleep(3)
            
            # 步骤6：分析DOM结构
            print("\n[步骤6] 分析DOM结构...")
            
            # 方法1：查找所有包含特定文本的元素
            print("\n[方法1] 查找包含'展现'和'阅读'的元素...")
            elements_with_stats = await page.evaluate("""
                () => {
                    const results = [];
                    const allDivs = document.querySelectorAll('div');
                    
                    for (const div of allDivs) {
                        const text = div.innerText || '';
                        if (text.includes('展现') && text.includes('阅读') && text.length > 30 && text.length < 500) {
                            results.push({
                                tagName: div.tagName,
                                className: div.className || '',
                                id: div.id || '',
                                textPreview: text.substring(0, 100),
                                textLength: text.length,
                                parentTagName: div.parentElement ? div.parentElement.tagName : '',
                                parentClassName: div.parentElement ? (div.parentElement.className || '') : ''
                            });
                            
                            if (results.length >= 10) break;
                        }
                    }
                    
                    return results;
                }
            """)
            
            print(f"  找到 {len(elements_with_stats)} 个包含统计数据的元素")
            for i, elem in enumerate(elements_with_stats[:5]):
                print(f"\n  元素 {i+1}:")
                print(f"    标签: {elem['tagName']}")
                print(f"    类名: {elem['className'][:100]}")
                print(f"    ID: {elem['id']}")
                print(f"    文本预览: {elem['textPreview']}")
                print(f"    父标签: {elem['parentTagName']}")
                print(f"    父类名: {elem['parentClassName'][:100]}")
            
            # 方法2：查找常见的列表容器
            print("\n\n[方法2] 查找常见的列表容器...")
            common_selectors = [
                'tbody',
                '.semi-table',
                '[class*="table"]',
                '[class*="list"]',
                '[class*="article"]',
                '[class*="content"]'
            ]
            
            for selector in common_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if len(elements) > 0:
                        print(f"\n  选择器 '{selector}': 找到 {len(elements)} 个元素")
                        
                        # 获取第一个元素的详细信息
                        if elements:
                            first_elem = elements[0]
                            tag = await first_elem.evaluate('el => el.tagName')
                            classes = await first_elem.evaluate('el => el.className || ""')
                            text = await first_elem.inner_text()
                            
                            print(f"    第一个元素:")
                            print(f"      标签: {tag}")
                            print(f"      类名: {classes[:100]}")
                            print(f"      文本长度: {len(text)}")
                            if len(text) > 0:
                                print(f"      文本预览: {text[:200]}")
                except Exception as e:
                    print(f"  选择器 '{selector}' 查询失败: {e}")
            
            # 方法3：保存页面HTML用于分析
            print("\n\n[方法3] 保存页面HTML...")
            html = await page.content()
            with open("logs/debug_dom.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  ✅ HTML已保存: logs/debug_dom.html (大小: {len(html)} 字符)")
            
            print("\n" + "=" * 80)
            print("调试完成！请检查上述输出和截图")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 关闭浏览器连接（不关闭Edge浏览器本身）
            await browser.close()
            print("\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(debug_dom_structure())
