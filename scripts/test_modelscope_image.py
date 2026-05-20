"""
测试魔搭社区图像生成模型（Qwen/Qwen-Image-2512）
验证新集成的图像生成服务是否正常工作
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.content.image_generator import ImageGenerator
from app.utils.logger import logger


async def test_modelscope_image_generation():
    """测试魔搭社区图像生成"""
    print("=" * 80)
    print("🎨 测试魔搭社区图像生成模型（Qwen/Qwen-Image-2512）")
    print("=" * 80)
    
    # 初始化图像生成器
    generator = ImageGenerator()
    
    # 测试用例
    test_cases = [
        {
            "name": "科技风格封面",
            "prompt": "人工智能科技背景，未来感，蓝色光效，高科技元素，4K超高清",
            "aspect_ratio": "16:9"
        },
        {
            "name": "财经风格封面",
            "prompt": "金融图表，股票走势图，金币，商业氛围，专业摄影",
            "aspect_ratio": "16:9"
        },
        {
            "name": "生活风格封面",
            "prompt": "温馨家居场景，阳光透过窗户，舒适生活，温暖色调",
            "aspect_ratio": "16:9"
        }
    ]
    
    # 执行测试
    success_count = 0
    fail_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{len(test_cases)}] {test_case['name']}")
        print(f"提示词: {test_case['prompt']}")
        print(f"比例: {test_case['aspect_ratio']}")
        
        try:
            result = await generator.generate_image(
                prompt=test_case['prompt'],
                style="realistic",
                aspect_ratio=test_case['aspect_ratio'],
                provider="modelscope"
            )
            
            if result.get("status") == "success":
                print(f"✅ 生成成功!")
                print(f"   图片路径: {result.get('image_path')}")
                print(f"   图片URL: {result.get('image_url')}")
                print(f"   提供商: {result.get('provider')}")
                print(f"   模型: {result.get('model')}")
                success_count += 1
            else:
                print(f"❌ 生成失败: {result.get('error')}")
                fail_count += 1
        
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            fail_count += 1
    
    # 输出统计结果
    print("\n" + "=" * 80)
    print(" 测试统计:")
    print(f"   成功: {success_count}/{len(test_cases)}")
    print(f"   失败: {fail_count}/{len(test_cases)}")
    print("=" * 80)
    
    if success_count > 0:
        print("\n✅ 魔搭社区图像生成模型集成成功！")
        return True
    else:
        print("\n❌ 所有测试用例均失败，请检查API配置和网络连接")
        return False


async def test_fallback_providers():
    """测试备用图像生成提供商"""
    print("\n" + "=" * 80)
    print("🔄 测试备用图像生成提供商")
    print("=" * 80)
    
    generator = ImageGenerator()
    
    # 测试阿里百炼（如果魔搭社区失败）
    print("\n[测试阿里百炼]")
    try:
        result = await generator.generate_image(
            prompt="科技未来感背景，蓝色光效，AI元素",
            style="realistic",
            aspect_ratio="16:9",
            provider="dashscope"
        )
        
        if result.get("status") == "success":
            print(f"✅ 阿里百炼生成成功: {result.get('image_path')}")
        else:
            print(f"⚠️ 阿里百炼生成失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 阿里百炼测试异常: {str(e)}")


async def main():
    """主测试流程"""
    print("\n🚀 开始图像生成模型测试...\n")
    
    # 测试魔搭社区
    modelscope_success = await test_modelscope_image_generation()
    
    # 如果魔搭社区失败，测试备用方案
    if not modelscope_success:
        print("\n⚠️ 魔搭社区测试失败，开始测试备用提供商...")
        await test_fallback_providers()
    
    print("\n" + "=" * 80)
    print("✅ 测试流程完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
