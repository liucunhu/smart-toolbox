"""
高级封面图功能 - 自动化测试（无需人工交互）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.content.ai_cover_generator import AICoverGenerator
from app.services.content.cover_template_library import get_template_library
from app.services.content.cover_ab_test import get_ab_tester


def test_ai_generation():
    """测试AI生成"""
    print("\n" + "="*80)
    print("🤖 测试1: AI智能生成封面图")
    print("="*80)
    
    generator = AICoverGenerator()
    
    # 测试1: 现代风格
    print("\n1️⃣  生成现代风格封面...")
    result1 = generator.generate_cover(
        title="Python自动化办公技巧",
        subtitle="10个实用方法提升效率",
        category="科技",
        style="modern"
    )
    
    if result1["status"] == "success":
        print(f"   ✅ 成功: {result1['file_path']}")
        print(f"   📊 大小: {result1['size_kb']}KB")
    else:
        print(f"   ❌ 失败: {result1.get('error')}")
        return False
    
    # 测试2: 极简风格
    print("\n2️⃣  生成极简风格封面...")
    result2 = generator.generate_cover(
        title="人工智能发展趋势",
        category="科技",
        style="minimal"
    )
    
    if result2["status"] == "success":
        print(f"   ✅ 成功: {result2['file_path']}")
    else:
        print(f"   ❌ 失败: {result2.get('error')}")
        return False
    
    # 测试3: 大胆风格
    print("\n3️⃣  生成大胆风格封面...")
    result3 = generator.generate_cover(
        title="财经投资指南",
        category="财经",
        style="bold"
    )
    
    if result3["status"] == "success":
        print(f"   ✅ 成功: {result3['file_path']}")
    else:
        print(f"   ❌ 失败: {result3.get('error')}")
        return False
    
    print("\n✅ AI生成测试通过!")
    return True


def test_template_library():
    """测试模板库"""
    print("\n" + "="*80)
    print("📚 测试2: 封面图模板库")
    print("="*80)
    
    library = get_template_library()
    
    # 测试1: 获取所有模板
    print("\n1️⃣  获取所有模板...")
    templates = library.get_all_templates()
    
    if len(templates) > 0:
        print(f"   ✅ 找到 {len(templates)} 个模板")
        for template in templates[:3]:  # 只显示前3个
            print(f"   📋 {template['id']}: {template['name']}")
    else:
        print(f"   ❌ 未找到模板")
        return False
    
    # 测试2: 使用模板生成
    print("\n2️⃣  使用模板生成封面...")
    result = library.generate_cover_from_template(
        template_id="tech_news",
        title="区块链技术解析"
    )
    
    if result["status"] == "success":
        print(f"   ✅ 成功: {result['file_path']}")
        print(f"   📋 模板: {result['template_name']}")
    else:
        print(f"   ❌ 失败: {result.get('error')}")
        return False
    
    print("\n✅ 模板库测试通过!")
    return True


def test_ab_testing():
    """测试A/B测试"""
    print("\n" + "="*80)
    print("📊 测试3: A/B测试框架")
    print("="*80)
    
    tester = get_ab_tester()
    
    # 测试1: 创建测试
    print("\n1️⃣  创建A/B测试...")
    cover_variants = [
        {"variant_id": "A", "file_path": "test_a.jpg", "style": "modern"},
        {"variant_id": "B", "file_path": "test_b.jpg", "style": "minimal"}
    ]
    
    result = tester.create_test(
        test_id="auto_test_001",
        article_title="测试文章",
        cover_variants=cover_variants
    )
    
    if result["status"] == "success":
        print(f"   ✅ 测试创建成功")
    else:
        print(f"   ❌ 创建失败: {result.get('error')}")
        return False
    
    # 测试2: 记录数据
    print("\n2️⃣  模拟用户行为...")
    for i in range(10):
        tester.record_impression("auto_test_001", "A", f"user_{i}")
    for i in range(5):
        tester.record_click("auto_test_001", "A", f"user_{i}")
    
    for i in range(10):
        tester.record_impression("auto_test_001", "B", f"user_{i+10}")
    for i in range(3):
        tester.record_click("auto_test_001", "B", f"user_{i+10}")
    
    print(f"   ✅ 变体A: 10曝光, 5点击")
    print(f"   ✅ 变体B: 10曝光, 3点击")
    
    # 测试3: 查看结果
    print("\n3️⃣  查看测试结果...")
    test_result = tester.get_test_results("auto_test_001")
    
    if test_result["status"] == "success":
        print(f"   ✅ 最佳变体: {test_result['best_variant']}")
        for vid, metrics in test_result["metrics"].items():
            print(f"   📊 变体{vid}: CTR={metrics['ctr']}%")
    else:
        print(f"   ❌ 失败: {test_result.get('error')}")
        return False
    
    # 清理
    tester.delete_test("auto_test_001")
    
    print("\n✅ A/B测试通过!")
    return True


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🚀 高级封面图功能 - 自动化测试")
    print("="*80)
    
    results = []
    
    try:
        # 测试AI生成
        result1 = test_ai_generation()
        results.append(("AI生成", result1))
        
        # 测试模板库
        result2 = test_template_library()
        results.append(("模板库", result2))
        
        # 测试A/B测试
        result3 = test_ab_testing()
        results.append(("A/B测试", result3))
        
    except Exception as e:
        print(f"\n❌ 测试错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 输出总结
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
