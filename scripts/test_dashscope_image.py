"""测试阿里百炼（DashScope）图像生成"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.content.image_generator import ImageGenerator


async def test_dashscope_image():
    """测试阿里百炼图像生成"""
    print("=" * 80)
    print("阿里百炼（DashScope）图像生成测试")
    print("=" * 80)
    
    generator = ImageGenerator()
    
    # 测试1: 生成文章配图
    print("\n📝 测试1: 生成科技主题配图")
    print("-" * 80)
    
    result = await generator.generate_image(
        prompt="AI technology, machine learning, neural network visualization, professional, high quality",
        style="realistic",
        aspect_ratio="16:9",
        provider="dashscope"
    )
    
    if result["status"] == "success":
        print(f"✅ 图像生成成功!")
        print(f"   路径: {result['image_path']}")
        print(f"   模型: {result.get('model', 'N/A')}")
        print(f"   提供商: {result.get('provider', 'N/A')}")
    else:
        print(f"❌ 图像生成失败: {result.get('error')}")
    
    # 测试2: 生成不同风格的图片
    print("\n🎨 测试2: 生成插画风格配图")
    print("-" * 80)
    
    result2 = await generator.generate_image(
        prompt="Smart home technology, modern living room with AI assistant, digital illustration",
        style="illustration",
        aspect_ratio="16:9",
        provider="dashscope"
    )
    
    if result2["status"] == "success":
        print(f"✅ 图像生成成功!")
        print(f"   路径: {result2['image_path']}")
    else:
        print(f"❌ 图像生成失败: {result2.get('error')}")
    
    # 测试3: 批量生成
    print("\n📦 测试3: 批量生成（3张）")
    print("-" * 80)
    
    prompts = [
        "Artificial intelligence robot helping humans, futuristic, optimistic",
        "Data center with servers and cloud computing, technology infrastructure",
        "Smartphone with AI chat interface, modern communication"
    ]
    
    results = await generator.generate_images_batch(
        prompts=prompts,
        style="realistic",
        aspect_ratio="16:9"
    )
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"✅ 成功生成 {success_count}/{len(results)} 张图像")
    
    for i, r in enumerate(results, 1):
        if r["status"] == "success":
            print(f"   图像{i}: {r['image_path']}")
        else:
            print(f"   图像{i}: ❌ {r.get('error')}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_dashscope_image())
