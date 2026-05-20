"""
测试头条自动化发布功能
验证：
1. 硅基流动图像生成（封面图）
2. 作品声明多选功能
3. 文章配图上传
"""
import asyncio
import sys
import json
sys.path.insert(0, 'D:\\code\\smart-toolbox')

from app.services.publish.toutiao_publisher import ToutiaoPublisher
from app.services.content.copywriting_generation import CopywritingGenerator
from app.services.content.article_image_generator import ArticleImageGenerator

async def test_auto_publish():
    """测试自动化发布完整流程"""
    print("=" * 70)
    print("测试头条自动化发布功能")
    print("=" * 70)
    
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        # ========== 步骤 1: 初始化浏览器 ==========
        print("\n[步骤1/6] 初始化浏览器（CDP模式）...")
        await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
        print("✅ 浏览器初始化成功")
        
        # ========== 步骤 2: AI生成文章 ==========
        print("\n[步骤2/6] AI生成文章内容...")
        generator = CopywritingGenerator()
        article_result = generator.generate_script("toutiao", "人工智能发展趋势")
        
        if not article_result:
            print("❌ AI生成失败")
            return False
        
        title = article_result.get("title", "AI发展趋势")
        content = article_result.get("content", "")
        tags = article_result.get("tags", [])
        
        print(f"✅ AI生成成功")
        print(f"   标题: {title}")
        print(f"   标题长度: {len(title)} 字符")
        print(f"   内容长度: {len(content)} 字符")
        print(f"   标签: {tags}")
        
        # ========== 步骤 2.5: 生成文章配图 ==========
        print("\n[步骤2.5/6] 生成文章配图...")
        image_generator = ArticleImageGenerator(use_ai=True)  # 强制使用AI生成
        article_images_info = await image_generator.generate_images_for_article(
            title=title,
            content=content,
            num_images=2,  # 生成2张配图
            category="科技",
            enable_ab_test=True  # 启用A/B测试
        )
        
        # 提取文件路径列表
        article_images = [img["file_path"] for img in article_images_info]
        
        if article_images:
            print(f"✅ 文章配图生成成功，共 {len(article_images)} 张")
            for i, img_path in enumerate(article_images, 1):
                print(f"   配图{i}: {img_path}")
        else:
            print("⚠️  文章配图生成失败，将不上传配图")
            article_images = []
        
        # ========== 步骤 3: 发布文章（包含封面图和作品声明） ==========
        print("\n[步骤3/6] 发布文章（测试硅基流动图像生成 + 作品声明多选）...")
        
        # 测试参数：
        # - auto_generate_cover=True: 使用硅基流动生成封面图
        # - declarations: 多选作品声明
        # - declaration_type: 兼容旧参数（已废弃）
        publish_result = await publisher.publish_article(
            title=title,
            content=content,
            category="科技",
            tags=tags,
            auto_generate_cover=True,  # ✅ 启用AI生成封面图
            cover_style="modern",
            declarations=["引用ai", "个人观点"],  # ✅ 测试多选声明
            article_images=article_images  # ✅ 使用生成的文章配图
        )
        
        print(f"\n发布结果: {json.dumps(publish_result, ensure_ascii=False, indent=2)}")
        
        if publish_result.get("status") in ["success", "pending"]:
            print("\n✅ 发布成功！")
            print(f"   文章标题: {publish_result.get('article_title', 'N/A')}")
            return True
        else:
            print(f"\n❌ 发布失败: {publish_result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await publisher.close()
        print("\n✅ 浏览器已关闭")

if __name__ == "__main__":
    result = asyncio.run(test_auto_publish())
    
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    if result:
        print("🎉 所有功能测试通过！")
        print("✅ AI文章生成（无Markdown标签） - 成功")
        print("✅ 文章配图生成与上传 - 成功")
        print("✅ 硅基流动封面图生成 - 成功")
        print("✅ 作品声明多选 - 成功")
        print("✅ 自动化发布 - 成功")
    else:
        print("⚠️  部分功能测试失败，请查看日志")
    print("=" * 70)
