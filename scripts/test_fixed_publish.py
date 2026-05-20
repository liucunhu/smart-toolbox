"""
测试修复后的头条发布功能
"""
import asyncio
from app.services.publish.toutiao_publisher import ToutiaoPublisher
from app.utils.logger import logger


async def test_fixed_publish():
    """测试修复后的发布功能"""
    
    print("="*80)
    print("🧪 测试修复后的头条发布功能")
    print("="*80)
    print()
    
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        # 1. 初始化浏览器
        print("\n[步骤 1] 初始化浏览器...")
        await publisher.initialize_browser()
        print("✅ 浏览器已初始化（非无头模式）")
        
        # 2. 登录
        print("\n[步骤 2] 登录头条账号...")
        login_result = await publisher.login_with_manual_input(
            username="17739848781",
            password="Hspc@2024"  # 请替换为实际密码
        )
        
        if login_result["status"] != "success":
            print(f"❌ 登录失败: {login_result}")
            return
        
        print(f"✅ 登录成功")
        
        # 3. 发布文章
        print("\n[步骤 3] 发布测试文章...")
        publish_result = await publisher.publish_article(
            title=f"【测试】修复后的发布功能_{asyncio.get_event_loop().time():.0f}",
            content="""这是一篇测试文章，用于验证修复后的发布功能。

主要改进：
1. 添加发布前后截图
2. 检测确认弹窗
3. 检测错误提示
4. 根据URL判断状态
5. 返回准确的状态信息

如果看到这篇文章，说明修复成功！
""",
            category="科技",
            tags=["测试", "自动化", "修复验证"]
        )
        
        print(f"\n{'='*80}")
        print(f"📊 发布结果:")
        print(f"{'='*80}")
        print(f"状态: {publish_result['status']}")
        print(f"标题: {publish_result.get('title', 'N/A')}")
        print(f"消息: {publish_result.get('message', 'N/A')}")
        if 'error' in publish_result:
            print(f"错误: {publish_result['error']}")
        print(f"{'='*80}")
        
        # 4. 根据状态给出建议
        print(f"\n💡 下一步操作:")
        if publish_result["status"] == "success":
            print("✅ 发布成功！")
            print("   请访问 https://mp.toutiao.com/ 查看已发布的文章")
        elif publish_result["status"] == "draft":
            print("⚠️  文章保存为草稿")
            print("   请访问 https://mp.toutiao.com/ → 内容管理 → 草稿箱")
            print("   手动点击发布按钮")
        elif publish_result["status"] == "failed":
            print("❌ 发布失败")
            print(f"   错误信息: {publish_result.get('error', '未知错误')}")
            print("   请查看 logs/ 目录下的截图文件分析原因")
        else:  # pending
            print("⏳ 状态待确认")
            print("   请访问 https://mp.toutiao.com/ 检查文章状态")
            print("   可能在: 已发布 / 草稿箱 / 审核中")
        
        # 5. 等待用户确认
        print(f"\n⏸️  浏览器将保持打开，请检查头条后台")
        print("   确认无误后，在此终端按回车关闭浏览器...")
        input()
        
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏸️  按回车关闭浏览器...")
        input()
    finally:
        await publisher.close()
        print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_fixed_publish())
