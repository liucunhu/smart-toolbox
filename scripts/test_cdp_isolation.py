"""
测试改进后的 CDP 模式 - 确保不影响日常 Edge 使用
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.publish.toutiao_publisher import ToutiaoPublisher


async def test_cdp_isolation():
    """测试 CDP 模式的隔离性"""
    print("=" * 80)
    print("测试 CDP 模式隔离性")
    print("=" * 80)
    print()
    print("这个测试将验证：")
    print("1. CDP 模式使用独立的临时用户数据目录")
    print("2. 不会影响您日常使用的 Edge 浏览器")
    print("3. 发布完成后自动清理临时目录")
    print()
    
    publisher = ToutiaoPublisher(account_id=999)  # 使用测试账号ID
    
    try:
        # 初始化 CDP 模式
        print("[1/3] 初始化 CDP 模式...")
        await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
        
        print(f"\n✅ CDP 模式启动成功！")
        print(f"   当前页面 URL: {publisher.page.url}")
        print(f"   用户数据目录: {publisher._cdp_user_data_dir}")
        
        # 检查目录是否存在
        if publisher._cdp_user_data_dir and os.path.exists(publisher._cdp_user_data_dir):
            print(f"   ✅ 临时目录已创建")
        else:
            print(f"   ⚠️  临时目录不存在（可能使用了现有浏览器）")
        
        print("\n[2/3] 等待 5 秒，您可以检查：")
        print("   - 是否有一个新的 Edge 窗口打开")
        print("   - 您的日常 Edge 浏览器是否正常运行")
        await asyncio.sleep(5)
        
        print("\n[3/3] 关闭 CDP 浏览器...")
        await publisher.close()
        
        # 检查临时目录是否被清理
        if hasattr(publisher, '_cdp_user_data_dir') and publisher._cdp_user_data_dir:
            if os.path.exists(publisher._cdp_user_data_dir):
                print(f"   ⚠️  临时目录仍然存在: {publisher._cdp_user_data_dir}")
                print(f"   （可能需要手动删除）")
            else:
                print(f"   ✅ 临时目录已自动清理")
        
        print("\n" + "=" * 80)
        print("✅ 测试完成！")
        print("=" * 80)
        print("\n现在您可以：")
        print("1. 正常使用 Edge 浏览器，不会被影响")
        print("2. 重新运行测试，会创建新的临时目录")
        print("3. 在前端界面使用一键发布功能")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保资源被清理
        if publisher.page or publisher.browser:
            await publisher.close()


if __name__ == "__main__":
    asyncio.run(test_cdp_isolation())
