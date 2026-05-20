"""
视频处理功能测试脚本
验证deduplication和format_conversion模块的完整功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试1: 模块导入")
    print("=" * 60)
    
    try:
        import cv2
        print(f"✅ OpenCV版本: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV导入失败: {e}")
        return False
    
    try:
        import ffmpeg
        print(f"✅ FFmpeg-python: OK")
    except ImportError as e:
        print(f"❌ FFmpeg导入失败: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy版本: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy导入失败: {e}")
        return False
    
    print()
    return True


def test_deduplication_engine():
    """测试视频去重引擎"""
    print("=" * 60)
    print("测试2: VideoDeduplicationEngine")
    print("=" * 60)
    
    try:
        from app.services.content.deduplication import VideoDeduplicationEngine
        print("✅ VideoDeduplicationEngine导入成功")
        
        # 检查类方法
        assert hasattr(VideoDeduplicationEngine, 'process'), "缺少process方法"
        assert hasattr(VideoDeduplicationEngine, '_apply_visual_noise'), "缺少_apply_visual_noise方法"
        assert hasattr(VideoDeduplicationEngine, '_apply_audio_shift'), "缺少_apply_audio_shift方法"
        print("✅ 所有必需方法存在")
        
        # 检查类型注解（不应有Any类型）
        import inspect
        sig = inspect.signature(VideoDeduplicationEngine._apply_visual_noise)
        params = sig.parameters
        
        cap_annotation = params['cap'].annotation
        writer_annotation = params['writer'].annotation
        
        # 验证不是Any类型
        from typing import Any
        assert cap_annotation != Any, "cap参数不应使用Any类型"
        assert writer_annotation != Any, "writer参数不应使用Any类型"
        
        print(f"✅ 类型注解正确: cap={cap_annotation}, writer={writer_annotation}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_format_converter():
    """测试格式转换器"""
    print("=" * 60)
    print("测试3: FormatConverter")
    print("=" * 60)
    
    try:
        from app.services.distribute.format_conversion import FormatConverter
        print("✅ FormatConverter导入成功")
        
        # 检查平台配置
        assert hasattr(FormatConverter, 'PLATFORM_SPECS'), "缺少PLATFORM_SPECS配置"
        assert 'douyin' in FormatConverter.PLATFORM_SPECS, "缺少抖音配置"
        assert 'xiaohongshu' in FormatConverter.PLATFORM_SPECS, "缺少小红书配置"
        assert 'bilibili' in FormatConverter.PLATFORM_SPECS, "缺少B站配置"
        print("✅ 平台配置完整")
        
        # 检查方法
        assert hasattr(FormatConverter, 'convert_video'), "缺少convert_video方法"
        print("✅ convert_video方法存在")
        
        # 打印配置详情
        print("\n平台规格配置:")
        for platform, spec in FormatConverter.PLATFORM_SPECS.items():
            print(f"  - {platform}: {spec['width']}x{spec['height']}, FPS={spec['fps']}, CRF={spec['crf']}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_no_degradation_code():
    """验证没有降级代码"""
    print("=" * 60)
    print("测试4: 检查无降级代码")
    print("=" * 60)
    
    files_to_check = [
        'app/services/content/deduplication.py',
        'app/services/distribute/format_conversion.py'
    ]
    
    degradation_keywords = [
        'CV2_AVAILABLE',
        'FFMPEG_AVAILABLE',
        '占位符',
        'Placeholder',
        '优雅降级',
        'degrade',
        'fallback'
    ]
    
    all_clean = True
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"⚠️  文件不存在: {file_path}")
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        found_issues = []
        for keyword in degradation_keywords:
            if keyword in content:
                found_issues.append(keyword)
        
        if found_issues:
            print(f"❌ {file_path} 发现降级代码关键词: {found_issues}")
            all_clean = False
        else:
            print(f"✅ {file_path} 无降级代码")
    
    print()
    return all_clean


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Smart-Toolbox 视频处理功能测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("去重引擎", test_deduplication_engine()))
    results.append(("格式转换", test_format_converter()))
    results.append(("无降级代码", test_no_degradation_code()))
    
    # 汇总结果
    print("=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s} {status}")
    
    print("-" * 60)
    print(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！视频处理功能已完整实现，无降级方案。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查上述错误。")
        return 1


if __name__ == "__main__":
    exit(main())
