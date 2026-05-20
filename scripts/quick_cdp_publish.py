"""
头条文章发布 - CDP模式（简化版）
使用真实Edge浏览器进行100%自动化发布
"""
import asyncio
import subprocess
from playwright.async_api import async_playwright


async def publish_article_cdp():
    """使用CDP连接真实Edge浏览器发布文章"""
    
    print("="*80)
    print("🚀 头条文章发布（CDP模式 - 真实Edge浏览器）")
    print("="*80)
    print("\n💡 方案说明：")
    print("   ✓ 启动真实Edge浏览器（带远程调试端口9222）")
    print("   ✓ Playwright通过CDP协议连接")
    print("   ✓ 100%真实浏览器环境，无自动化特征")
    print("   ✓ 自动完成：登录 → 填写 → 发布")
    print()
    
    # Edge浏览器路径
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    debug_port = 9222
    
    # ========== 步骤1：启动Edge浏览器 ==========
    print(f"[1/5] 启动Edge浏览器（调试端口 {debug_port}）...")
    
    # ★★★ 关键修复：不关闭所有Edge进程，只检查CDP端口是否可用 ★★★
    import socket
    cdp_available = False
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', debug_port))
        if result == 0:
            cdp_available = True
            print(f"   ⚠️  CDP端口 {debug_port} 已被占用，尝试复用现有浏览器")
        sock.close()
    except:
        pass
    
    if not cdp_available:
        # 只有当CDP端口未被占用时，才启动新浏览器
        print("   启动新的Edge浏览器实例...")
        
        # 先关闭已有的Edge进程（仅当需要启动新浏览器时）
        print("   关闭已存在的Edge进程...")
        try:
            subprocess.run("taskkill /F /IM msedge.exe", shell=True, capture_output=True, timeout=5)
            await asyncio.sleep(2)
        except:
            pass
        
        # 启动带远程调试的Edge
        user_data_dir = "./edge_profile_toutiao_cdp"
        cmd = [
            edge_path,
            f'--remote-debugging-port={debug_port}',
            f'--user-data-dir={user_data_dir}',
            'https://mp.toutiao.com/'
        ]
        
        process = subprocess.Popen(cmd)
        print("✅ Edge浏览器已启动")
        print("   等待浏览器完全启动（5秒）...")
        await asyncio.sleep(5)
    else:
        print("   ✅ 使用现有的Edge浏览器实例")
    
    async with async_playwright() as p:
        # ========== 步骤2：连接到Edge浏览器 ==========
        print(f"\n[2/5] 连接到Edge浏览器（CDP端口 {debug_port}）...")
        
        try:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")
            
            # 获取第一个context和page
            contexts = browser.contexts
            if not contexts:
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai"
                )
            else:
                context = contexts[0]
            
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
            
            print("✅ 已连接到真实Edge浏览器")
            print(f"   当前URL: {page.url}")
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            print("\n可能的原因：")
            print("   1. Edge浏览器未成功启动")
            print("   2. 调试端口9222被占用")
            print("   3. Edge路径不正确")
            return
        
        # ========== 步骤3：检查登录状态 ==========
        print("\n[3/5] 检查登录状态...")
        
        current_url = page.url
        if "login" in current_url or "sso" in current_url:
            print("⚠️  检测到未登录状态")
            print("\n👤 请在浏览器窗口中手动完成登录：")
            print("   - 可以使用扫码登录")
            print("   - 或者手机号+验证码登录")
            print("   - 或者账号密码登录")
            print("\n💡 提示：登录后系统会自动检测并继续")
            print("   如果长时间未检测到，请在此终端按回车继续...")
            
            # 等待用户登录（最多等待120秒）
            login_detected = False
            for attempt in range(60):
                await asyncio.sleep(2)
                current_url = page.url
                
                # 检测策略1: URL包含 profile
                if "profile" in current_url and "login" not in current_url:
                    login_detected = True
                    print(f"\n✅ 检测到登录成功（URL匹配）")
                    break
                
                # 检测策略2: 页面标题包含关键词
                try:
                    title = await page.title()
                    if any(keyword in title for keyword in ['头条号', '工作台', '首页']):
                        if "login" not in current_url:
                            login_detected = True
                            print(f"\n✅ 检测到登录成功（页面标题: {title}）")
                            break
                except:
                    pass
                
                # 每10次输出一次提示
                if (attempt + 1) % 10 == 0:
                    remaining = 120 - (attempt + 1) * 2
                    print(f"   ⏳ 等待登录中... 剩余 {remaining} 秒")
            
            if not login_detected:
                print("\n⚠️  超时未检测到登录，但将继续尝试（可能已登录）")
                input("确认已登录后按回车继续...")
        else:
            print("✅ 已登录")
        
        # ========== 步骤4：访问发布页面 ==========
        print("\n[4/5] 访问发布页面...")
        
        publish_url = "https://mp.toutiao.com/profile_v4/graphic/publish"
        current_url = page.url
        
        if publish_url not in current_url:
            print(f"   当前URL: {current_url}")
            print("   正在跳转到发布页面...")
            
            try:
                await page.goto(publish_url, timeout=60000, wait_until='domcontentloaded')
            except Exception as e:
                if "interrupted" in str(e) or "navigation" in str(e).lower():
                    print("   ⚠️  导航冲突（可能正在自动跳转），等待页面稳定...")
                else:
                    raise e
        else:
            print("   ✅ 已在发布页面")
        
        # 等待页面完全加载
        print("   等待页面完全加载（10秒）...")
        await asyncio.sleep(10)
        
        # 验证页面加载状态
        print("\n   验证页面加载状态...")
        page_info = await page.evaluate("""
            () => {
                const editor = document.querySelector('div[contenteditable="true"]');
                const titleInput = document.querySelector('input[placeholder*="标题"]');
                
                let publishBtn = null;
                document.querySelectorAll('button').forEach(btn => {
                    if (btn.textContent.includes('预览并发布')) publishBtn = btn;
                });
                
                return {
                    editor: !!editor,
                    title: !!titleInput,
                    button: !!publishBtn,
                    url: window.location.href
                };
            }
        """)
        
        print(f"   编辑器: {'✅' if page_info['editor'] else '❌'}")
        print(f"   标题框: {'✅' if page_info['title'] else '❌'}")
        print(f"   发布按钮: {'✅' if page_info['button'] else '❌'}")
        
        if not page_info['editor'] or not page_info['button']:
            print("\n⚠️  页面可能未完整加载，但仍将尝试发布")
        
        # ========== 步骤5：填写内容并发布 ==========
        print("\n[5/5] 填写内容并发布...")
        
        # 准备文章内容
        title = "人工智能技术发展趋势分析"
        content = """这是一篇关于人工智能技术发展的深度分析文章。

近年来，人工智能技术取得了长足的进步。机器学习、深度学习、自然语言处理、计算机视觉等技术正在改变我们的生活和工作方式。

人工智能的发展速度令人惊叹。从AlphaGo到GPT系列模型，AI技术在各个领域都取得了突破性进展。特别是在内容创作、智能客服、自动驾驶等领域，AI已经展现出强大的能力。

自然语言处理技术的进步尤为显著。大语言模型能够理解和生成人类语言，这在智能写作、机器翻译、对话系统等场景都有广泛应用。

计算机视觉技术也在快速发展。图像识别、目标检测、视频分析等技术正在各个行业发挥重要作用。从安防监控到医疗影像，从工业自动化到智能交通，计算机视觉的应用场景越来越广泛。

同时，AI技术的伦理和安全问题也日益受到关注。如何在推动技术发展的同时，确保AI的安全性和可控性，是我们需要共同思考的问题。

未来，人工智能将继续快速发展，在更多领域发挥重要作用。我们应该积极拥抱AI技术，同时也要注意其带来的挑战和风险。
"""
        
        print(f"   标题: {title}")
        print(f"   内容长度: {len(content)} 字")
        
        # 填写标题
        print("\n   步骤1: 填写标题...")
        try:
            title_input = await page.query_selector('input[placeholder="请输入标题"]')
            if not title_input:
                title_input = await page.query_selector('textarea[placeholder*="标题"]')
            
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
                print("   ✅ 标题已填写")
            else:
                print("   ❌ 未找到标题输入框")
        except Exception as e:
            print(f"   ❌ 填写标题失败: {e}")
        
        # 填写正文
        print("\n   步骤2: 填写正文...")
        try:
            editor = await page.query_selector('div[contenteditable="true"]')
            if editor:
                await editor.fill(content)
                await asyncio.sleep(2)
                print(f"   ✅ 正文已填写（{len(content)} 字）")
            else:
                print("   ❌ 未找到编辑器")
        except Exception as e:
            print(f"   ❌ 填写正文失败: {e}")
        
        # 选择分类
        print("\n   步骤3: 选择分类...")
        try:
            category_selectors = [
                'text=科技',
                'span:has-text("科技")',
                'div:has-text("科技")'
            ]
            
            category_selected = False
            for selector in category_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        await elem.click()
                        await asyncio.sleep(1)
                        print("   ✅ 已选择分类：科技")
                        category_selected = True
                        break
                except:
                    continue
            
            if not category_selected:
                print("   ⚠️  未找到分类选项，使用默认分类")
        except Exception as e:
            print(f"   ⚠️  选择分类失败: {e}")
        
        # 点击发布按钮
        print("\n   步骤4: 点击发布按钮...")
        try:
            # 查找发布按钮
            publish_button = None
            button_selectors = [
                'button:has-text("预览并发布")',
                'button:has-text("发布")',
                'button[type="submit"]'
            ]
            
            for selector in button_selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn and await btn.is_visible():
                        publish_button = btn
                        break
                except:
                    continue
            
            if publish_button:
                print("   找到发布按钮，准备点击...")
                
                # 滚动到按钮位置
                await publish_button.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                
                # 点击发布
                await publish_button.click()
                print("   ✅ 已点击发布按钮")
                
                # 等待发布结果
                print("\n   步骤5: 等待发布结果...")
                await asyncio.sleep(5)
                
                # 检查是否有成功提示
                try:
                    success_indicators = [
                        'text=发布成功',
                        'text=提交成功',
                        '.ant-message-success',
                        '[class*="success"]'
                    ]
                    
                    for indicator in success_indicators:
                        try:
                            elem = await page.query_selector(indicator)
                            if elem and await elem.is_visible():
                                print("   ✅ 检测到发布成功提示！")
                                break
                        except:
                            continue
                except:
                    pass
                
                print("\n" + "="*80)
                print("🎉 发布流程已完成！")
                print("="*80)
                print("\n📋 下一步操作：")
                print("   1. 检查浏览器窗口中的提示消息")
                print("   2. 查看截图文件（logs目录）")
                print("   3. 访问头条后台确认文章状态")
                print("   4. 如需验证，运行: python scripts\\verify_toutiao_publish.py")
                
            else:
                print("   ❌ 未找到发布按钮")
                print("   💡 可能需要手动点击发布")
        
        except Exception as e:
            print(f"   ❌ 发布失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 保存截图
        print("\n   保存页面截图...")
        try:
            screenshot_path = f"logs/cdp_publish_{int(asyncio.get_event_loop().time())}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"   ✅ 截图已保存: {screenshot_path}")
        except Exception as e:
            print(f"   ⚠️  截图失败: {e}")
        
        # 保持浏览器打开，让用户检查结果
        print("\n" + "="*80)
        print("⏸️  浏览器将保持打开状态")
        print("="*80)
        print("\n请检查：")
        print("   1. 浏览器中的发布结果")
        print("   2. logs目录下的截图文件")
        print("\n确认无误后，在此终端按回车关闭浏览器...")
        input()


if __name__ == "__main__":
    try:
        asyncio.run(publish_article_cdp())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n按回车退出...")
        input()
