"""
测试使用CDP连接Edge浏览器并抓取文章数据
"""
import asyncio
from playwright.async_api import async_playwright

async def test_cdp_analytics():
    """测试CDP连接和文章数据抓取"""
    print("=" * 80)
    print("测试CDP连接Edge浏览器并抓取文章数据")
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
            await page.screenshot(path="logs/cdp_analytics.png", full_page=True)
            print("✅ 已截图: logs/cdp_analytics.png")
            
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
            
            # 步骤6：尝试抓取文章数据
            print("\n[步骤6] 尝试抓取文章数据...")
            
            articles_data = await page.evaluate("""
                () => {
                    const articles = [];
                    
                    // 方法1：尝试查找文章列表项
                    const possibleSelectors = [
                        // 表格行
                        'tbody tr',
                        '.semi-table-row',
                        '[class*="table-row"]',
                        
                        // 文章卡片
                        '.article-item',
                        '[class*="article-item"]',
                        '[class*="content-item"]',
                        '[class*="list-item"]',
                        
                        // 通用选择器
                        '[class*="item"]',
                        '[class*="row"]'
                    ];
                    
                    let articleElements = [];
                    
                    for (const selector of possibleSelectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 2) {
                            console.log(`选择器 ${selector} 找到 ${elements.length} 个元素`);
                            articleElements = Array.from(elements);
                            break;
                        }
                    }
                    
                    // 如果上面的选择器都没找到，尝试更宽松的选择器
                    if (articleElements.length === 0) {
                        // 查找包含文章标题和统计数据的元素
                        const allDivs = document.querySelectorAll('div');
                        for (const div of allDivs) {
                            const text = div.innerText || '';
                            // 检查是否包含文章特征：标题 + 统计数据
                            if (text.includes('展现') && text.includes('阅读') && text.length > 20 && text.length < 300) {
                                articleElements.push(div);
                                if (articleElements.length >= 50) break;
                            }
                        }
                    }
                    
                    console.log(`找到 ${articleElements.length} 个文章元素`);
                    
                    // 遍历文章元素
                    articleElements.forEach((element, index) => {
                        if (index >= 50) return; // 最多50篇
                        
                        try {
                            const text = element.innerText || '';
                            
                            // 过滤：必须包含统计数据
                            if (!text.includes('展现') || !text.includes('阅读')) {
                                return;
                            }
                            
                            // 提取标题（通常是第一行较长的文本，且不包含统计数据关键词）
                            const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                            let title = '';
                            
                            for (const line of lines) {
                                // 标题应该：长度>5，不包含统计关键词
                                if (line.length > 5 && 
                                    !line.includes('展现') && 
                                    !line.includes('阅读') && 
                                    !line.includes('点赞') && 
                                    !line.includes('评论') &&
                                    !line.includes('已发布')) {
                                    title = line;
                                    break;
                                }
                            }
                            
                            if (!title || title.length < 5) {
                                return;
                            }
                            
                            // 提取数字（展现、阅读、点赞、评论）
                            const numbers = text.match(/\\d+/g) || [];
                            
                            if (numbers.length >= 4) {
                                articles.push({
                                    title: title.substring(0, 100),
                                    read_count: parseInt(numbers[1]) || 0,
                                    like_count: parseInt(numbers[2]) || 0,
                                    comment_count: parseInt(numbers[3]) || 0,
                                    share_count: parseInt(numbers[4]) || 0,
                                    publish_time: new Date().toISOString()
                                });
                            }
                        } catch (e) {
                            console.error(`处理文章 ${index} 失败:`, e);
                        }
                    });
                    
                    console.log(`成功提取 ${articles.length} 篇文章`);
                    return articles;
                }
            """)
            
            print(f"\n✅ 成功抓取 {len(articles_data)} 篇文章")
            
            if len(articles_data) > 0:
                print("\n" + "=" * 80)
                print("文章数据示例（前3篇）：")
                print("=" * 80)
                for i, article in enumerate(articles_data[:3]):
                    print(f"\n文章 {i+1}:")
                    print(f"  标题: {article['title']}")
                    print(f"  阅读: {article['read_count']}")
                    print(f"  点赞: {article['like_count']}")
                    print(f"  评论: {article['comment_count']}")
            else:
                print("\n️  未抓取到文章数据")
                print("可能原因：")
                print("  1. 账号没有发布过文章")
                print("  2. 页面仍在登录状态")
                print("  3. 头条页面结构已更新")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 关闭浏览器连接（不关闭Edge浏览器本身）
            await browser.close()
            print("\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_cdp_analytics())
