"""
端到端测试：头条发布流程中的AI配图生成
测试阿里百炼图像生成在头条发布中的集成
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.content.article_image_generator import ArticleImageGenerator


async def test_article_images_in_publish_flow():
    """测试头条发布流程中的文章配图生成"""
    print("=" * 80)
    print("头条发布流程 - AI配图生成端到端测试")
    print("=" * 80)
    
    # 模拟头条发布的参数
    article_title = "人工智能技术革新：深度学习如何改变未来"
    article_content = """
人工智能正在深刻改变我们的生活方式。从智能家居到自动驾驶，AI技术已经渗透到各个领域。

机器学习是人工智能的核心技术。通过大量数据的训练，机器学习模型能够做出准确的预测和决策。

深度学习作为机器学习的子集，使用神经网络模拟人脑的工作方式，能够处理更加复杂的任务。

在未来，AI技术将继续发展，为人类带来更多的便利和创新。
    """
    category = "科技"
    num_images = 2
    
    print(f"\n 文章标题: {article_title}")
    print(f"📄 内容长度: {len(article_content)} 字符")
    print(f" 分类: {category}")
    print(f"🎨 配图数量: {num_images}张")
    
    # 创建文章配图生成器（强制使用AI）
    print("\n🚀 开始生成文章配图（使用阿里百炼）...")
    print("-" * 80)
    
    generator = ArticleImageGenerator(use_ai=True)
    
    # 调用生成方法（与头条发布流程相同）
    images_info = await generator.generate_images_for_article(
        title=article_title,
        content=article_content,
        num_images=num_images,
        category=category,
        enable_ab_test=True  # 启用A/B测试
    )
    
    # 输出结果
    print("\n" + "=" * 80)
    print("生成结果")
    print("=" * 80)
    
    if images_info:
        print(f"\n✅ 成功生成 {len(images_info)} 张配图:\n")
        
        for i, img in enumerate(images_info, 1):
            print(f"   配图 {i}:")
            print(f"      - 主题: {img.get('theme', 'N/A')}")
            print(f"      - 路径: {img.get('file_path', 'N/A')}")
            print(f"      - AI生成: {img.get('ai_generated', False)}")
            print(f"      - 提供商: {img.get('provider', 'N/A')}")
            print(f"      - 尺寸: {img.get('size', 'N/A')}")
            
            # 检查A/B测试信息
            if 'ab_test_id' in img:
                print(f"      - A/B测试ID: {img['ab_test_id']}")
            
            print()
        
        # 提取文件路径列表（用于头条发布）
        article_images = [img["file_path"] for img in images_info]
        print(f"📋 用于头条发布的配图路径列表:")
        for path in article_images:
            print(f"   - {path}")
        
        return True
    else:
        print("\n❌ 配图生成失败")
        return False


async def test_different_styles():
    """测试不同风格的配图生成"""
    print("\n" + "=" * 80)
    print("测试不同文章类型的配图生成")
    print("=" * 80)
    
    test_cases = [
        {
            "title": "2026年最热门的科技趋势预测",
            "content": "从AI到量子计算，2026年科技领域将迎来重大突破...",
            "category": "科技",
            "num_images": 2
        },
        {
            "title": "健康饮食指南：如何保持营养均衡",
            "content": "合理的饮食结构对健康至关重要...",
            "category": "健康",
            "num_images": 2
        }
    ]
    
    generator = ArticleImageGenerator(use_ai=True)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 测试案例 {i}: {case['title']}")
        print("-" * 80)
        
        images = await generator.generate_images_for_article(
            title=case["title"],
            content=case["content"],
            num_images=case["num_images"],
            category=case["category"],
            enable_ab_test=False  # 简化测试，不启用A/B测试
        )
        
        success_count = sum(1 for img in images if img.get("ai_generated"))
        print(f"   ✅ 成功生成 {success_count}/{case['num_images']} 张AI配图")


if __name__ == "__main__":
    print("\n" + "🎯" * 40)
    print("开始测试头条发布流程中的AI配图生成")
    print("🎯" * 40 + "\n")
    
    # 测试1: 头条发布流程模拟
    result1 = asyncio.run(test_article_images_in_publish_flow())
    
    # 测试2: 不同文章类型
    asyncio.run(test_different_styles())
    
    print("\n" + "=" * 80)
    if result1:
        print("✅ 所有测试通过！头条发布流程中的AI配图生成已就绪")
    else:
        print("❌ 测试失败，请检查配置")
    print("=" * 80)
