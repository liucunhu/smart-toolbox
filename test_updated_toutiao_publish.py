"""
测试更新后的头条发布功能（包含文章配图）
基于成功的集成测试脚本 test_cdp_auto_publish.py
"""
import asyncio
from app.services.publish.toutiao_publisher import ToutiaoPublisher


async def test_toutiao_publish_with_images():
    """测试头条发布功能，包含文章配图"""
    
    # 创建发布器实例
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        # 1. 初始化浏览器（使用CDP模式连接真实Edge浏览器）
        print("\n=== 第一步：初始化浏览器 ===")
        await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
        
        # 2. 智能登录（先尝试Cookie，失败后等待手动登录）
        print("\n=== 第二步：智能登录 ===")
        login_success = await publisher.smart_login()
        
        if not login_success:
            print("❌ 登录失败")
            return
        
        print("✅ 登录成功")
        
        # 3. 准备测试数据
        title = "AI技术革新：机器学习如何改变我们的生活"
        content = """
人工智能正在以前所未有的速度发展，深刻影响着我们的日常生活。
从智能手机到自动驾驶，从医疗诊断到金融分析，AI技术已经渗透到各个领域。

机器学习的进步使得计算机能够处理复杂的任务，识别图像、理解语言、预测趋势。
这些技术的应用不仅提高了效率，还创造了全新的商业模式和服务体验。

未来，随着算法的不断优化和计算能力的提升，AI将继续推动社会进步。
我们需要积极拥抱这一变革，同时关注伦理和安全问题。
"""
        
        # 准备文章配图（使用测试图片）
        import os
        article_images = [
            os.path.abspath("uploads/covers/test_image_1.jpg"),
            os.path.abspath("uploads/covers/test_image_2.jpg")
        ]
        
        # 检查图片是否存在
        existing_images = [img for img in article_images if os.path.exists(img)]
        if not existing_images:
            print("⚠️  测试图片不存在，跳过配图测试")
            article_images = None
        else:
            print(f"✅ 找到 {len(existing_images)} 张测试图片")
            article_images = existing_images
        
        # 4. 发布文章（包含文章配图）
        print("\n=== 第三步：发布文章 ===")
        result = await publisher.publish_article(
            title=title,
            content=content,
            category="科技",
            tags=["AI", "机器学习", "人工智能"],
            auto_generate_cover=True,  # 自动生成封面图
            cover_style="modern",
            declaration_type="personal_opinion",  # 仅个人观点
            article_images=article_images  # 传入文章配图
        )
        
        print(f"\n发布结果: {result}")
        
        if result["status"] == "success":
            print("\n✅ 测试成功！文章已发布")
        elif result["status"] == "pending":
            print("\n⚠️  发布请求已发送，请检查头条后台确认状态")
        else:
            print(f"\n❌ 发布失败: {result.get('error')}")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 5. 关闭浏览器
        print("\n=== 第四步：关闭浏览器 ===")
        await publisher.close()
        print("✅ 浏览器已关闭")


if __name__ == "__main__":
    print("=" * 80)
    print("测试更新后的头条发布功能（包含文章配图）")
    print("=" * 80)
    
    asyncio.run(test_toutiao_publish_with_images())
