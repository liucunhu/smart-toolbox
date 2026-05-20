"""
测试番茄小说功能模块
验证模型、API和Publisher的基本功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_models():
    """测试数据模型"""
    print("=" * 80)
    print("测试1: 数据模型导入")
    print("=" * 80)
    
    try:
        from app.models import PlatformEnum, Novel, Chapter, FanqieAnalytics
        
        # 检查PlatformEnum是否包含FANQIE
        assert hasattr(PlatformEnum, 'FANQIE'), "PlatformEnum缺少FANQIE枚举"
        print(f"✅ PlatformEnum.FANQIE = {PlatformEnum.FANQIE.value}")
        
        # 检查Novel模型
        print(f"✅ Novel模型字段:")
        print(f"   - title: {Novel.title}")
        print(f"   - category: {Novel.category}")
        print(f"   - total_chapters: {Novel.total_chapters}")
        
        # 检查Chapter模型
        print(f"✅ Chapter模型字段:")
        print(f"   - chapter_number: {Chapter.chapter_number}")
        print(f"   - content: {Chapter.content}")
        print(f"   - word_count: {Chapter.word_count}")
        
        # 检查FanqieAnalytics模型
        print(f"✅ FanqieAnalytics模型字段:")
        print(f"   - daily_reads: {FanqieAnalytics.daily_reads}")
        print(f"   - completion_rate: {FanqieAnalytics.completion_rate}")
        
        print("\n✅ 数据模型测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 数据模型测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_publisher():
    """测试Publisher类"""
    print("=" * 80)
    print("测试2: FanqiePublisher类")
    print("=" * 80)
    
    try:
        from app.services.publish.fanqie_publisher import FanqiePublisher
        
        # 创建实例
        publisher = FanqiePublisher(account_id=1)
        print(f"✅ FanqiePublisher实例创建成功")
        print(f"   - account_id: {publisher.account_id}")
        print(f"   - browser: {publisher.browser}")
        print(f"   - page: {publisher.page}")
        
        # 检查方法是否存在
        methods = [
            'initialize_browser',
            'login_with_cookies',
            'create_novel',
            'publish_chapter',
            'fetch_analytics',
            'close'
        ]
        
        for method in methods:
            assert hasattr(publisher, method), f"缺少方法: {method}"
            print(f"✅ 方法存在: {method}")
        
        print("\n✅ Publisher类测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Publisher类测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_api_imports():
    """测试API端点导入"""
    print("=" * 80)
    print("测试3: API端点导入")
    print("=" * 80)
    
    try:
        # 尝试导入endpoints模块
        from app.api.v1 import endpoints
        
        # 检查是否有番茄相关的函数
        api_functions = [
            'fanqie_login',
            'create_fanqie_novel',
            'publish_fanqie_chapter',
            'auto_publish_fanqie_chapter',
            'get_fanqie_analytics',
            'get_account_novels',
            'get_novel_chapters'
        ]
        
        for func_name in api_functions:
            assert hasattr(endpoints, func_name), f"缺少API函数: {func_name}"
            func = getattr(endpoints, func_name)
            print(f"✅ API函数存在: {func_name}")
            if hasattr(func, '__doc__'):
                doc = func.__doc__
                if doc:
                    print(f"   描述: {doc.strip().split(chr(10))[0]}")
        
        print("\n✅ API端点导入测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ API端点导入测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_frontend_files():
    """测试前端文件"""
    print("=" * 80)
    print("测试4: 前端文件")
    print("=" * 80)
    
    try:
        # 检查Vue组件
        vue_file = "frontend/src/views/FanqieManagement.vue"
        assert os.path.exists(vue_file), f"文件不存在: {vue_file}"
        print(f"✅ Vue组件存在: {vue_file}")
        
        # 检查文件大小
        file_size = os.path.getsize(vue_file)
        print(f"   文件大小: {file_size} bytes")
        
        # 读取文件内容检查关键部分
        with open(vue_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_sections = [
            '<template>',
            '<script setup',
            '<style',
            'fanqie-management',
            'handleLogin',
            'handleCreateNovel',
            'handlePublishChapter'
        ]
        
        for section in required_sections:
            assert section in content, f"Vue组件缺少: {section}"
            print(f"✅ Vue组件包含: {section}")
        
        # 检查路由配置
        router_file = "frontend/src/router/index.ts"
        with open(router_file, 'r', encoding='utf-8') as f:
            router_content = f.read()
        
        assert 'FanqieManagement' in router_content, "路由未导入FanqieManagement"
        assert "path: 'fanqie'" in router_content or 'path: "fanqie"' in router_content, "路由未配置fanqie路径"
        print(f"✅ 路由配置正确")
        
        # 检查菜单配置
        layout_file = "frontend/src/components/MainLayout.vue"
        with open(layout_file, 'r', encoding='utf-8') as f:
            layout_content = f.read()
        
        assert '番茄小说' in layout_content, "菜单未添加番茄小说入口"
        assert '/fanqie' in layout_content, "菜单链接不正确"
        print(f"✅ 菜单配置正确")
        
        print("\n✅ 前端文件测试通过\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 前端文件测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("🚀 开始测试番茄小说功能模块")
    print("\n")
    
    results = []
    
    # 运行测试
    results.append(("数据模型", test_models()))
    results.append(("Publisher类", test_publisher()))
    results.append(("API端点", test_api_imports()))
    results.append(("前端文件", test_frontend_files()))
    
    # 打印总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} {status}")
    
    print("-" * 80)
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！番茄小说功能模块已成功集成。\n")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误信息。\n")
        return 1


if __name__ == "__main__":
    exit(main())
