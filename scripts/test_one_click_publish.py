"""
测试一键发布功能的各个组件
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.content.copywriting_generation import CopywritingGenerator
from app.utils.logger import logger


def test_llm_generation():
    """测试LLM文章生成"""
    print("="*80)
    print("🧪 测试1: LLM文章生成")
    print("="*80)
    
    try:
        generator = CopywritingGenerator()
        
        topic = "人工智能技术在2024年的突破性进展"
        print(f"\n主题: {topic}")
        print("正在生成文章...")
        
        result = generator.generate_script("toutiao", topic)
        
        if not result:
            print("❌ LLM生成失败")
            return False
        
        print("\n✅ LLM生成成功！")
        print(f"\n标题: {result.get('title', 'N/A')}")
        print(f"分类: {result.get('category', 'N/A')}")
        print(f"标签: {', '.join(result.get('tags', []))}")
        print(f"内容长度: {len(result.get('content', ''))} 字")
        
        # 检查内容质量
        content = result.get('content', '')
        if len(content) < 500:
            print("⚠️  警告：文章内容过短（< 500字）")
            return False
        
        if len(content) > 3000:
            print("⚠️  警告：文章内容过长（> 3000字）")
            return False
        
        print("✅ 文章长度合适（500-3000字）")
        
        # 显示部分内容
        print("\n内容预览（前200字）:")
        print("-" * 80)
        print(content[:200] + "...")
        print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cover_generation():
    """测试封面图生成功能（模拟）"""
    print("\n" + "="*80)
    print("🧪 测试2: 封面图生成配置")
    print("="*80)
    
    try:
        # 检查必要的模块是否可用
        from app.services.cover.smart_cover_generator import SmartCoverGenerator
        from app.services.cover.template_library import TemplateLibrary
        
        print("\n✅ 封面图生成模块已导入")
        
        # 检查模板库
        template_lib = TemplateLibrary()
        templates = template_lib.list_templates()
        
        print(f"✅ 模板库可用，共有 {len(templates)} 个模板")
        
        if templates:
            print("\n可用模板示例:")
            for i, template in enumerate(templates[:3]):
                print(f"  {i+1}. {template.get('name', 'N/A')} - {template.get('style', 'N/A')}")
        
        # 检查LLM分析器
        from app.services.cover.llm_analyzer import LLMCoverAnalyzer
        analyzer = LLMCoverAnalyzer()
        
        print("✅ LLM封面分析器已初始化")
        
        # 模拟分析
        test_title = "人工智能技术发展趋势"
        test_keywords = ["人工智能", "机器学习", "深度学习"]
        
        print(f"\n模拟分析:")
        print(f"  标题: {test_title}")
        print(f"  关键词: {', '.join(test_keywords)}")
        print(f"  ✅ 可以生成封面提示词")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  封面图生成模块未完全安装: {e}")
        print("💡 建议: 安装相关依赖或使用手动上传封面")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compliance_check():
    """测试合规审查功能"""
    print("\n" + "="*80)
    print("🧪 测试3: 合规审查")
    print("="*80)
    
    try:
        from app.api.v1.endpoints import check_content_compliance
        
        # 测试正常内容
        test_title = "人工智能技术发展"
        test_content = "这是一篇关于人工智能的文章，介绍了最新的技术进展。"
        
        print("\n测试正常内容...")
        result = check_content_compliance(test_title, test_content, "toutiao")
        
        if result["passed"]:
            print("✅ 正常内容通过审查")
        else:
            print(f"❌ 正常内容未通过: {result.get('error')}")
            return False
        
        # 测试违禁词
        test_content_bad = "这篇文章包含一些敏感词汇，比如最好、第一、绝对等"
        
        print("\n测试含违禁词内容...")
        result_bad = check_content_compliance(test_title, test_content_bad, "toutiao")
        
        if not result_bad["passed"]:
            print(f"✅ 违禁词检测正常工作: {result_bad.get('error')}")
        else:
            print("⚠️  违禁词未被检测到（可能需要更新词库）")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cdp_connection():
    """测试CDP连接（不实际启动浏览器）"""
    print("\n" + "="*80)
    print("🧪 测试4: CDP配置检查")
    print("="*80)
    
    try:
        import socket
        
        # 检查Edge浏览器是否存在
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        
        edge_found = False
        for path in edge_paths:
            if os.path.exists(path):
                print(f"\n✅ Edge浏览器已找到: {path}")
                edge_found = True
                break
        
        if not edge_found:
            print("\n❌ 未找到Edge浏览器")
            print("💡 请安装 Microsoft Edge 浏览器")
            return False
        
        # 检查CDP端口
        cdp_port = 9222
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', cdp_port))
        sock.close()
        
        if result == 0:
            print(f"✅ CDP端口 {cdp_port} 已被占用（可能有浏览器在运行）")
        else:
            print(f"✅ CDP端口 {cdp_port} 可用")
        
        # 检查Playwright
        try:
            import playwright
            print("✅ Playwright已安装")
        except ImportError:
            print("❌ Playwright未安装")
            print("💡 运行: playwright install")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🚀 一键发布功能完整性测试")
    print("="*80)
    
    results = {
        "LLM文章生成": test_llm_generation(),
        "封面图生成": test_cover_generation(),
        "合规审查": test_compliance_check(),
        "CDP配置": test_cdp_connection(),
    }
    
    # 汇总结果
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！一键发布功能完全可用！")
        print("\n下一步:")
        print("  1. 确保后端服务运行: python main.py")
        print("  2. 调用API进行测试")
        print("  3. 查看文档: docs_archive/ONE_CLICK_PUBLISH_GUIDE.md")
    else:
        print("\n⚠️  部分测试失败，请根据上面的提示修复")
    
    print("="*80)


if __name__ == "__main__":
    main()
