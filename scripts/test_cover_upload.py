"""
测试头条自动发布上传封面图功能
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.publish.toutiao_publisher import ToutiaoPublisher


async def test_cover_upload():
    """测试封面图上传功能"""
    print("=" * 80)
    print("🧪 测试头条自动发布上传封面图功能")
    print("=" * 80)
    
    # 创建测试用的封面图文件（如果不存在）
    test_cover_path = "test_cover.jpg"
    if not os.path.exists(test_cover_path):
        print(f"\n⚠️  测试封面图文件不存在: {test_cover_path}")
        print("请先准备一个测试用的封面图文件（jpg/png格式）")
        print("并将其放置在项目根目录下，命名为 test_cover.jpg")
        return
    
    print(f"\n✅ 找到测试封面图: {test_cover_path}")
    print(f"   文件大小: {os.path.getsize(test_cover_path)} bytes")
    
    # 初始化发布器
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        # 1. 初始化浏览器
        print("\n[步骤 1] 初始化浏览器...")
        await publisher.initialize_browser()
        print("✅ 浏览器初始化成功")
        
        # 2. 登录（需要手动完成）
        print("\n[步骤 2] 请登录头条账号...")
        print("   系统会打开浏览器，请手动完成登录")
        print("   登录完成后，按回车继续...")
        input("   按回车继续...")
        
        # 3. 发布文章（带封面图）
        print("\n[步骤 3] 发布文章（带封面图）...")
        result = await publisher.publish_article(
            title="测试封面图上传功能",
            content="这是一篇测试文章，用于验证封面图上传功能是否正常工作。\n\n文章内容测试...",
            category="科技",
            tags=["测试", "封面图"],
            cover_image_path=test_cover_path
        )
        
        print(f"\n{'='*80}")
        print(f"📊 发布结果:")
        print(f"{'='*80}")
        print(f"状态: {result['status']}")
        if 'title' in result:
            print(f"标题: {result['title']}")
        if 'message' in result:
            print(f"消息: {result['message']}")
        if 'error' in result:
            print(f"错误: {result['error']}")
        print(f"{'='*80}")
        
        if result['status'] == 'success':
            print("\n🎉 测试成功！封面图上传功能正常工作")
        elif result['status'] == 'pending':
            print("\n⏳ 发布状态待确认，请检查头条后台")
        else:
            print(f"\n❌ 测试失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭浏览器
        print("\n[清理] 关闭浏览器...")
        await publisher.close()
        print("✅ 浏览器已关闭")


if __name__ == "__main__":
    print("\n💡 使用说明:")
    print("1. 准备一个测试用的封面图文件（jpg/png格式）")
    print("2. 将文件放置在项目根目录下，命名为 test_cover.jpg")
    print("3. 运行此脚本进行测试")
    print("\n" + "="*80 + "\n")
    
    asyncio.run(test_cover_upload())
