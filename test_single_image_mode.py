"""
测试头条发布封面图选择功能
验证是否正确选择"单图"模式而不是"无图/无封面"
"""
import asyncio
from app.services.publish.toutiao_publisher import ToutiaoPublisher


async def test_single_image_mode():
    """测试单图模式选择"""
    
    print("="*80)
    print("🧪 测试头条封面图选择功能")
    print("="*80)
    print("\n测试目标：")
    print("1. ✅ 确保选择'单图'模式")
    print("2. ✅ 避免选择'无图/无封面'模式")
    print("="*80)
    
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        # 步骤1: 初始化浏览器
        print("\n[步骤 1] 初始化浏览器...")
        await publisher.initialize_browser()
        print("✅ 浏览器已初始化")
        
        # 步骤2: 登录（需要手动完成）
        print("\n[步骤 2] 请登录头条账号...")
        login_result = await publisher.login_with_manual_input(
            username="your_account",  # 请替换为实际账号
            password="your_password"  # 请替换为实际密码
        )
        
        if login_result["status"] != "success":
            print(f"❌ 登录失败: {login_result}")
            return
        
        print("✅ 登录成功")
        
        # 步骤3: 访问发布页面
        print("\n[步骤 3] 访问发布页面...")
        await publisher.page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", 
                                  wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print("✅ 发布页面已加载")
        
        # 步骤4: 测试单图模式选择
        print("\n[步骤 4] 测试单图模式选择...")
        result = await publisher._select_single_image_mode()
        
        if result:
            print("✅ 单图模式选择成功！")
        else:
            print("❌ 单图模式选择失败！")
        
        # 步骤5: 验证当前状态
        print("\n[步骤 5] 验证当前封面模式...")
        verification = await publisher.page.evaluate("""
            () => {
                const radios = document.querySelectorAll('input[type="radio"]');
                const modes = [];
                
                for (const radio of radios) {
                    const parent = radio.parentElement;
                    if (parent) {
                        const text = parent.textContent || '';
                        if (text.includes('单图') || text.includes('三图') || text.includes('无图')) {
                            modes.push({
                                mode: text.trim(),
                                checked: radio.checked
                            });
                        }
                    }
                }
                
                return modes;
            }
        """)
        
        print("\n📊 当前封面模式状态:")
        for mode in verification:
            status = "✅ 已选中" if mode['checked'] else "⚪ 未选中"
            print(f"   {mode['mode']}: {status}")
        
        # 检查是否选中了单图
        single_image_selected = any(m['mode'].includes('单图') and m['checked'] for m in verification)
        no_image_selected = any(m['mode'].includes('无图') and m['checked'] for m in verification)
        
        print("\n" + "="*80)
        if single_image_selected:
            print("✅ 测试通过：'单图'模式已正确选择！")
        elif no_image_selected:
            print("❌ 测试失败：错误地选择了'无图'模式！")
        else:
            print("⚠️  测试警告：无法确定当前选择的模式")
        print("="*80)
        
        # 保持浏览器打开，方便人工检查
        print("\n💡 提示：浏览器将保持打开状态，您可以人工检查页面")
        print("   按回车键关闭浏览器并结束测试...")
        input()
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await publisher.close()
        print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_single_image_mode())
