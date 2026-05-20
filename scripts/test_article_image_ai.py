"""
测试文章配图AI生成和A/B测试集成功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.content.article_image_generator import get_article_image_generator
from app.services.content.cover_ab_test import get_ab_tester


async def test_ai_image_generation():
    """测试AI生成文章配图"""
    print("=" * 80)
    print("测试1: AI生成文章配图")
    print("=" * 80)
    
    # 创建生成器（强制使用AI）
    generator = get_article_image_generator(use_ai=True)
    
    # 测试文章
    title = "人工智能技术革新：深度学习如何改变未来"
    content = """
    人工智能正在快速发展，深度学习技术在各个领域都取得了突破性进展。
    
    在计算机视觉领域，卷积神经网络(CNN)已经能够实现超越人类的图像识别能力。
    
    自然语言处理方面，Transformer架构的提出让机器翻译、文本生成等任务达到了新的高度。
    
    强化学习在游戏AI、机器人控制等领域也展现出巨大的潜力。
    
    未来，随着算力的提升和算法的优化，AI技术将会更加普及和智能化。
    """
    
    print(f"\n📝 文章标题: {title}")
    print(f"📄 内容长度: {len(content)} 字符")
    
    # 生成配图
    print("\n🎨 开始生成AI配图...")
    images = await generator.generate_images_for_article(
        title=title,
        content=content,
        num_images=3,
        category="科技",
        enable_ab_test=True  # 启用A/B测试
    )
    
    print(f"\n✅ 生成了 {len(images)} 张配图:")
    for i, img in enumerate(images, 1):
        print(f"\n   配图 {i}:")
        print(f"      - 主题: {img.get('theme', 'N/A')}")
        print(f"      - 路径: {img.get('file_path', 'N/A')}")
        print(f"      - AI生成: {img.get('ai_generated', False)}")
        print(f"      - 提供商: {img.get('provider', 'N/A')}")
        if 'ab_test_id' in img:
            print(f"      - A/B测试ID: {img['ab_test_id']}")
    
    return images


def test_ab_test_results():
    """测试A/B测试结果查询"""
    print("\n" + "=" * 80)
    print("测试2: A/B测试结果查询")
    print("=" * 80)
    
    ab_tester = get_ab_tester()
    
    # 获取所有测试
    all_tests = ab_tester.get_all_tests()
    
    if not all_tests:
        print("\n⚠️  暂无A/B测试记录")
        return
    
    print(f"\n📊 找到 {len(all_tests)} 个A/B测试:\n")
    
    for test in all_tests:
        print(f"测试ID: {test['test_id']}")
        print(f"文章标题: {test['article_title']}")
        print(f"状态: {test['test_status']}")
        print(f"最佳变体: {test.get('best_variant', 'N/A')}")
        print(f"最佳CTR: {test.get('best_ctr', 0)}%")
        
        print("\n变体详情:")
        for variant in test['variants']:
            variant_id = variant['variant_id']
            metrics = test['metrics'][variant_id]
            print(f"  变体 {variant_id}:")
            print(f"    - 风格: {variant.get('style', 'N/A')}")
            print(f"    - 描述: {variant.get('description', 'N/A')}")
            print(f"    - 曝光数: {metrics['impressions']}")
            print(f"    - 点击数: {metrics['clicks']}")
            print(f"    - CTR: {metrics['ctr']}%")
        
        print("-" * 80)


async def test_traditional_fallback():
    """测试传统方式降级"""
    print("\n" + "=" * 80)
    print("测试3: 传统方式降级（当AI失败时）")
    print("=" * 80)
    
    # 创建生成器（不使用AI）
    generator = get_article_image_generator(use_ai=False)
    
    title = "测试传统配图生成"
    content = "这是一篇测试文章的内容。"
    
    print(f"\n📝 文章标题: {title}")
    print("🎨 使用传统PIL方式生成配图...")
    
    images = await generator.generate_images_for_article(
        title=title,
        content=content,
        num_images=2,
        category="科技",
        enable_ab_test=False  # 不启用A/B测试
    )
    
    print(f"\n✅ 生成了 {len(images)} 张配图:")
    for i, img in enumerate(images, 1):
        print(f"\n   配图 {i}:")
        print(f"      - 主题: {img.get('theme', 'N/A')}")
        print(f"      - 路径: {img.get('file_path', 'N/A')}")
        print(f"      - AI生成: {img.get('ai_generated', False)}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("文章配图AI生成 + A/B测试集成测试")
    print("=" * 80)
    
    try:
        # 测试1: AI生成
        images = await test_ai_image_generation()
        
        # 测试2: A/B测试结果
        test_ab_test_results()
        
        # 测试3: 传统方式降级
        await test_traditional_fallback()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
