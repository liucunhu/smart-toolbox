"""
智能封面图生成测试脚本
测试AI自动生成和模板生成功能
"""
import asyncio
import requests
import json


def test_smart_cover_generation():
    """测试智能封面图生成"""
    print("\n" + "="*80)
    print("🎨 测试智能封面图生成功能")
    print("="*80)
    
    base_url = "http://localhost:8000/api/v1"
    
    # 测试1: AI智能生成封面图
    print("\n1️⃣  测试1: AI智能生成封面图")
    print("-" * 80)
    
    response = requests.post(
        f"{base_url}/content/generate-ai-cover",
        data={
            "title": "人工智能技术发展趋势分析",
            "content": "近年来，人工智能技术取得了长足的进步。机器学习、深度学习、自然语言处理等技术正在改变我们的生活。",
            "category": "科技",
            "tags": ["AI", "技术", "趋势"],
            "count": 3
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "success":
        best_cover = result.get("best_cover", {})
        print(f"\n✅ AI封面生成成功！")
        print(f"   标题: {best_cover.get('title')}")
        print(f"   风格: {best_cover.get('style')}")
        print(f"   配色: {best_cover.get('color_scheme')}")
        print(f"   文件: {best_cover.get('file_path')}")
        print(f"   大小: {best_cover.get('size_kb')} KB")
        print(f"   评分: {best_cover.get('score')}")
        print(f"   生成数量: {result.get('total_generated')}")
    else:
        print(f"❌ 生成失败: {result.get('error')}")
    
    # 测试2: 使用模板生成封面图
    print("\n2️⃣  测试2: 使用模板生成封面图")
    print("-" * 80)
    
    response = requests.post(
        f"{base_url}/content/generate-template-cover",
        data={
            "title": "Python编程入门教程",
            "category": "教育",
            "template_id": "education"
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "success":
        print(f"\n✅ 模板封面生成成功！")
        print(f"   标题: {result.get('title')}")
        print(f"   模板: {result.get('template_name')}")
        print(f"   文件: {result.get('file_path')}")
        print(f"   大小: {result.get('size_kb')} KB")
    else:
        print(f"❌ 生成失败: {result.get('error')}")
    
    # 测试3: 获取模板列表
    print("\n3️⃣  测试3: 获取封面模板列表")
    print("-" * 80)
    
    response = requests.get(
        f"{base_url}/content/cover-templates/list",
        params={"category": "科技"}
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"模板总数: {result.get('total')}")
    
    if result.get("templates"):
        print("\n可用模板:")
        for template in result["templates"]:
            print(f"  - ID: {template['id']}, 名称: {template['name']}, "
                  f"分类: {template['category']}, 风格: {template['style']}")
    else:
        print("⚠️  没有找到模板")
    
    # 测试4: 不同分类的封面生成
    print("\n4️⃣  测试4: 不同分类的封面生成")
    print("-" * 80)
    
    test_cases = [
        {"title": "股市投资技巧", "category": "财经"},
        {"title": "健康饮食指南", "category": "健康"},
        {"title": "电影推荐榜单", "category": "娱乐"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 生成 {case['category']} 类封面...")
        
        response = requests.post(
            f"{base_url}/content/generate-ai-cover",
            data={
                "title": case["title"],
                "category": case["category"],
                "count": 1
            }
        )
        
        result = response.json()
        
        if result.get("status") == "success":
            best_cover = result.get("best_cover", {})
            print(f"   ✅ 成功 - 风格: {best_cover.get('style')}, "
                  f"配色: {best_cover.get('color_scheme')}, "
                  f"评分: {best_cover.get('score')}")
        else:
            print(f"   ❌ 失败: {result.get('error')}")
    
    print("\n" + "="*80)
    print("📊 测试完成")
    print("="*80)
    print("\n💡 提示:")
    print("   - AI生成会根据内容自动选择最佳风格和配色")
    print("   - 模板生成适合快速创建统一风格的封面")
    print("   - 生成的图片会自动压缩优化")
    print("   - 查看 uploads/ai_covers 目录查看生成的图片")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 智能封面图生成测试")
    print("="*80)
    
    try:
        test_smart_cover_generation()
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
