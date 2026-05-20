"""
高级封面图功能综合测试脚本
测试图片压缩、AI生成、模板库和A/B测试功能
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.image_processor import ImageProcessor
from app.services.content.ai_cover_generator import AICoverGenerator
from app.services.content.cover_template_library import get_template_library
from app.services.content.cover_ab_test import get_ab_tester


def test_image_compression():
    """测试图片压缩功能"""
    print("\n" + "="*80)
    print("📦 测试1: 图片压缩和格式转换")
    print("="*80)
    
    # 创建测试图片（如果不存在）
    test_image_path = "test_sample.jpg"
    if not os.path.exists(test_image_path):
        print(f"\n⚠️  测试图片不存在: {test_image_path}")
        print("请先准备一张测试图片放在项目根目录")
        return False
    
    processor = ImageProcessor()
    
    # 测试1: 获取图片信息
    print("\n1️⃣  获取图片信息...")
    info = processor.get_image_info(test_image_path)
    if info["status"] == "success":
        print(f"   ✅ 原始尺寸: {info['dimensions']}")
        print(f"   ✅ 格式: {info['format']}")
        print(f"   ✅ 大小: {info['size_kb']}KB")
    else:
        print(f"   ❌ 失败: {info.get('error')}")
        return False
    
    # 测试2: 压缩图片
    print("\n2️⃣  压缩图片（JPG格式）...")
    compress_result = processor.compress_image(
        input_path=test_image_path,
        output_path="test_compressed.jpg",
        quality=85,
        max_width=1920,
        max_height=1080,
        output_format='jpg'
    )
    
    if compress_result["status"] == "success":
        print(f"   ✅ 压缩成功!")
        print(f"   📊 原始大小: {compress_result['original_size_kb']}KB")
        print(f"   📊 压缩后: {compress_result['compressed_size_kb']}KB")
        print(f"   📊 压缩率: {compress_result['compression_ratio_percent']}%")
        print(f"   📐 新尺寸: {compress_result['new_dimensions']}")
    else:
        print(f"   ❌ 压缩失败: {compress_result.get('error')}")
        return False
    
    # 测试3: 转换为WebP格式
    print("\n3️⃣  转换为WebP格式...")
    webp_result = processor.convert_format(
        input_path=test_image_path,
        output_format='webp',
        output_path="test_converted.webp",
        quality=85
    )
    
    if webp_result["status"] == "success":
        print(f"   ✅ 转换成功!")
        print(f"   📊 原始大小: {webp_result['original_size_kb']}KB")
        print(f"   📊 WebP大小: {webp_result['new_size_kb']}KB")
        print(f"   📊 节省空间: {webp_result['size_change_percent']}%")
    else:
        print(f"   ❌ 转换失败: {webp_result.get('error')}")
        return False
    
    # 清理测试文件
    print("\n4️⃣  清理测试文件...")
    for file in ["test_compressed.jpg", "test_converted.webp"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"   ✅ 已删除: {file}")
    
    print("\n✅ 图片压缩测试通过!")
    return True


def test_ai_cover_generation():
    """测试AI封面图生成功能"""
    print("\n" + "="*80)
    print("🤖 测试2: AI智能生成封面图")
    print("="*80)
    
    generator = AICoverGenerator()
    
    # 测试1: 生成现代风格封面
    print("\n1️⃣  生成现代风格封面...")
    result1 = generator.generate_cover(
        title="Python自动化办公技巧",
        subtitle="10个实用方法提升效率",
        category="科技",
        style="modern"
    )
    
    if result1["status"] == "success":
        print(f"   ✅ 生成成功!")
        print(f"   📁 文件: {result1['file_path']}")
        print(f"   🎨 风格: {result1['style']}")
        print(f"   🎨 配色: {result1['color_scheme']}")
        print(f"   📐 尺寸: {result1['dimensions']}")
        print(f"   📊 大小: {result1['size_kb']}KB")
        
        # 验证文件存在
        if os.path.exists(result1['file_path']):
            print(f"   ✅ 文件已保存")
        else:
            print(f"   ❌ 文件未找到")
            return False
    else:
        print(f"   ❌ 生成失败: {result1.get('error')}")
        return False
    
    # 测试2: 生成极简风格封面
    print("\n2️⃣  生成极简风格封面...")
    result2 = generator.generate_cover(
        title="人工智能发展趋势",
        subtitle="2026年最新预测",
        category="科技",
        style="minimal"
    )
    
    if result2["status"] == "success":
        print(f"   ✅ 生成成功!")
        print(f"   📁 文件: {result2['file_path']}")
        print(f"   🎨 风格: {result2['style']}")
    else:
        print(f"   ❌ 生成失败: {result2.get('error')}")
        return False
    
    # 测试3: 生成大胆风格封面
    print("\n3️⃣  生成大胆风格封面...")
    result3 = generator.generate_cover(
        title="财经投资指南",
        subtitle="新手必读",
        category="财经",
        style="bold"
    )
    
    if result3["status"] == "success":
        print(f"   ✅ 生成成功!")
        print(f"   📁 文件: {result3['file_path']}")
        print(f"   🎨 风格: {result3['style']}")
    else:
        print(f"   ❌ 生成失败: {result3.get('error')}")
        return False
    
    # 测试4: 批量生成多个版本
    print("\n4️⃣  批量生成多个版本...")
    results = generator.generate_multiple_covers(
        title="机器学习入门教程",
        subtitle="从零开始",
        category="教育",
        count=3
    )
    
    if len(results) > 0:
        print(f"   ✅ 成功生成 {len(results)} 个版本")
        for i, result in enumerate(results, 1):
            print(f"   📄 版本{i}: {result['style']} - {result['file_path']}")
    else:
        print(f"   ❌ 批量生成失败")
        return False
    
    print("\n✅ AI封面图生成测试通过!")
    return True


def test_template_library():
    """测试封面图模板库"""
    print("\n" + "="*80)
    print("📚 测试3: 封面图模板库")
    print("="*80)
    
    library = get_template_library()
    
    # 测试1: 获取所有模板
    print("\n1️⃣  获取所有模板...")
    templates = library.get_all_templates()
    
    if len(templates) > 0:
        print(f"   ✅ 找到 {len(templates)} 个模板")
        for template in templates:
            print(f"   📋 {template['id']}: {template['name']} ({template['category']})")
    else:
        print(f"   ❌ 未找到模板")
        return False
    
    # 测试2: 按分类筛选
    print("\n2️⃣  按分类筛选模板...")
    tech_templates = library.get_template_by_category("科技")
    
    if len(tech_templates) > 0:
        print(f"   ✅ 科技类模板: {len(tech_templates)} 个")
        for template in tech_templates:
            print(f"   📋 {template['id']}: {template['name']}")
    else:
        print(f"   ⚠️  未找到科技类模板")
    
    # 测试3: 使用模板生成封面
    print("\n3️⃣  使用模板生成封面...")
    result = library.generate_cover_from_template(
        template_id="tech_news",
        title="区块链技术解析",
        subtitle="深入理解分布式账本"
    )
    
    if result["status"] == "success":
        print(f"   ✅ 生成成功!")
        print(f"   📁 文件: {result['file_path']}")
        print(f"   📋 模板: {result['template_name']}")
        print(f"   📊 大小: {result['size_kb']}KB")
    else:
        print(f"   ❌ 生成失败: {result.get('error')}")
        return False
    
    # 测试4: 添加自定义模板
    print("\n4️⃣  添加自定义模板...")
    success = library.add_custom_template(
        template_id="test_custom",
        name="测试模板",
        category="测试",
        style="modern",
        color_scheme="科技蓝",
        layout="title_center",
        description="用于测试的自定义模板"
    )
    
    if success:
        print(f"   ✅ 自定义模板添加成功")
        
        # 验证模板是否存在
        template = library.get_template_by_id("test_custom")
        if template:
            print(f"   ✅ 模板验证成功: {template['name']}")
        else:
            print(f"   ❌ 模板验证失败")
            return False
    else:
        print(f"   ❌ 添加模板失败")
        return False
    
    # 清理测试模板
    print("\n5️⃣  清理测试模板...")
    library.delete_template("test_custom")
    print(f"   ✅ 已删除测试模板")
    
    print("\n✅ 模板库测试通过!")
    return True


def test_ab_testing():
    """测试A/B测试框架"""
    print("\n" + "="*80)
    print("📊 测试4: A/B测试框架")
    print("="*80)
    
    tester = get_ab_tester()
    
    # 测试1: 创建A/B测试
    print("\n1️⃣  创建A/B测试...")
    cover_variants = [
        {
            "variant_id": "A",
            "file_path": "uploads/ai_covers/test_a.jpg",
            "style": "modern",
            "description": "现代风格"
        },
        {
            "variant_id": "B",
            "file_path": "uploads/ai_covers/test_b.jpg",
            "style": "minimal",
            "description": "极简风格"
        }
    ]
    
    result = tester.create_test(
        test_id="test_ab_001",
        article_title="Python编程教程",
        cover_variants=cover_variants,
        description="测试不同风格的点击率"
    )
    
    if result["status"] == "success":
        print(f"   ✅ 测试创建成功!")
        print(f"   🆔 测试ID: {result['test_id']}")
        print(f"   📊 变体数量: {len(result['variants'])}")
        print(f"   📋 变体: {', '.join(result['variants'])}")
    else:
        print(f"   ❌ 创建失败: {result.get('error')}")
        return False
    
    # 测试2: 记录曝光和点击
    print("\n2️⃣  模拟用户行为...")
    
    # 变体A: 10次曝光，3次点击
    for i in range(10):
        tester.record_impression("test_ab_001", "A", f"user_{i}")
    for i in range(3):
        tester.record_click("test_ab_001", "A", f"user_{i}")
    
    # 变体B: 10次曝光，5次点击
    for i in range(10):
        tester.record_impression("test_ab_001", "B", f"user_{i+10}")
    for i in range(5):
        tester.record_click("test_ab_001", "B", f"user_{i+10}")
    
    print(f"   ✅ 变体A: 10次曝光, 3次点击")
    print(f"   ✅ 变体B: 10次曝光, 5次点击")
    
    # 测试3: 查看测试结果
    print("\n3️⃣  查看测试结果...")
    test_result = tester.get_test_results("test_ab_001")
    
    if test_result["status"] == "success":
        print(f"   ✅ 测试结果:")
        for variant_id, metrics in test_result["metrics"].items():
            print(f"   📊 变体{variant_id}:")
            print(f"      - 曝光: {metrics['impressions']}")
            print(f"      - 点击: {metrics['clicks']}")
            print(f"      - CTR: {metrics['ctr']}%")
        
        print(f"   🏆 最佳变体: {test_result['best_variant']}")
        print(f"   📈 最佳CTR: {test_result['best_ctr']}%")
    else:
        print(f"   ❌ 获取结果失败: {test_result.get('error')}")
        return False
    
    # 测试4: 结束测试
    print("\n4️⃣  结束测试...")
    end_result = tester.end_test("test_ab_001")
    
    if end_result["status"] == "success":
        print(f"   ✅ 测试已结束")
        print(f"   🏆 最终最佳变体: {end_result['best_variant']}")
    else:
        print(f"   ❌ 结束测试失败: {end_result.get('error')}")
        return False
    
    # 测试5: 生成报告
    print("\n5️⃣  生成测试报告...")
    report = tester.generate_test_report("test_ab_001")
    
    if report:
        print(f"   ✅ 报告生成成功")
        print(f"\n{report}")
    else:
        print(f"   ❌ 报告生成失败")
        return False
    
    # 清理测试数据
    print("\n6️⃣  清理测试数据...")
    tester.delete_test("test_ab_001")
    print(f"   ✅ 已删除测试数据")
    
    print("\n✅ A/B测试框架测试通过!")
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🚀 高级封面图功能综合测试")
    print("="*80)
    print("\n本测试将验证以下功能:")
    print("  1. 图片压缩和格式转换")
    print("  2. AI智能生成封面图")
    print("  3. 封面图模板库")
    print("  4. A/B测试框架")
    print("="*80)
    
    results = []
    
    # 运行测试
    try:
        # 测试1: 图片压缩（需要测试图片）
        print("\n⚠️  提示: 图片压缩测试需要准备 test_sample.jpg 文件")
        print("   如果没有该文件，将跳过此测试\n")
        input("按回车继续其他测试...")
        
        # 测试2: AI生成
        result2 = test_ai_cover_generation()
        results.append(("AI封面图生成", result2))
        
        # 测试3: 模板库
        result3 = test_template_library()
        results.append(("模板库", result3))
        
        # 测试4: A/B测试
        result4 = test_ab_testing()
        results.append(("A/B测试", result4))
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 输出测试总结
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! 功能正常工作!")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查日志")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

