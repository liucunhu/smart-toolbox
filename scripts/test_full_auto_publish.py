"""
全自动头条发布测试 - 使用智能登录
"""
import asyncio
from app.services.publish.toutiao_publisher import ToutiaoPublisher
from app.db.session import SessionLocal


async def test_full_auto_publish():
    """测试全自动发布（智能登录）"""
    
    print("="*80)
    print("🚀 全自动头条发布测试（智能登录版）")
    print("="*80)
    
    # 从数据库获取账号信息
    db = SessionLocal()
    try:
        from app.models import Account
        account = db.query(Account).filter(Account.id == 1).first()
        
        if not account:
            print("❌ 账号不存在")
            return
        
        print(f"\n📋 账号信息:")
        print(f"   ID: {account.id}")
        print(f"   用户名: {account.username}")
        print(f"   平台: {account.platform}")
        print(f"   有Cookie: {'是' if account.cookies else '否'}")
        
    finally:
        db.close()
    
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        # 步骤 1: 初始化浏览器
        print("\n[步骤 1] 初始化浏览器...")
        await publisher.initialize_browser()
        print("✅ 浏览器已初始化（带反检测）")
        
        # 步骤 2: 智能登录
        print("\n[步骤 2] 智能登录...")
        login_success = await publisher.smart_login(cookies=account.cookies)
        
        if not login_success:
            print("❌ 登录失败")
            return
        
        # 保存新的Cookie（仅当Cookie不太大时）
        new_cookies = await publisher.context.cookies()
        import json
        cookies_str = json.dumps(new_cookies)
        
        # 只有当 Cookie 不太大时才保存（< 50000 字符）
        if len(cookies_str) < 50000:
            db = SessionLocal()
            try:
                from app.models import Account
                db_account = db.query(Account).filter(Account.id == 1).first()
                if db_account:
                    db_account.cookies = cookies_str
                    db.commit()
                    print(f"✅ 已保存新的Cookie ({len(new_cookies)}个)")
            except Exception as e:
                print(f"⚠️  保存Cookie失败: {e}")
            finally:
                db.close()
        else:
            print(f"⚠️  Cookie数据太大（{len(cookies_str)}字符），不保存到数据库")
            print("💡 使用系统Edge配置，Cookie已自动保留")
        
        # 步骤 3: 生成文章内容
        print("\n[步骤 3] 准备文章内容...")
        # 头条标题限制2-30字，必须至少2个字
        test_title = "人工智能技术发展趋势分析"  # 12个字，符合要求
        test_content = """这是一篇关于人工智能技术发展的深度分析文章。

近年来，人工智能技术取得了长足的进步，从机器学习到深度学习，从自然语言处理到计算机视觉，AI正在改变着我们的生活方式和工作模式。

首先，让我们来看看机器学习领域的最新进展。随着算力的提升和数据的积累，机器学习算法的性能不断提升。特别是深度学习技术，在图像识别、语音识别、自然语言处理等领域都取得了突破性进展。

其次，自然语言处理技术的进步尤为显著。大语言模型的出现，让机器能够理解和生成人类语言，这在智能客服、自动翻译、内容生成等场景都有广泛应用。

再次，计算机视觉技术也在快速发展。从人脸识别到物体检测，从图像生成到视频分析，计算机视觉正在各个行业发挥着重要作用。

最后，AI技术的伦理和安全问题也日益受到关注。如何在推动技术发展的同时，确保AI的安全性和可控性，是我们需要共同思考的问题。

总的来说，人工智能技术正处于快速发展阶段，未来将在更多领域发挥重要作用。我们应该积极拥抱AI技术，同时也要注意其带来的挑战和风险。

希望通过本文的分析，能够帮助大家更好地了解人工智能技术的发展趋势和应用前景。
"""
        print(f"✅ 标题: {test_title}")
        print(f"✅ 内容长度: {len(test_content)} 字")
        
        # 步骤 4: 发布文章
        print("\n[步骤 4] 发布文章...")
        publish_result = await publisher.publish_article(
            title=test_title,
            content=test_content,
            category="科技",
            tags=["测试", "自动化"]
        )
        
        print(f"\n{'='*80}")
        print(f"📊 发布结果:")
        print(f"{'='*80}")
        print(f"状态: {publish_result['status']}")
        if 'title' in publish_result:
            print(f"标题: {publish_result['title']}")
        if 'message' in publish_result:
            print(f"消息: {publish_result['message']}")
        if 'error' in publish_result:
            print(f"错误: {publish_result['error']}")
        print(f"{'='*80}")
        
        # 步骤 5: 验证发布
        if publish_result['status'] == 'success':
            print("\n⏳ 等待3秒后验证发布结果...")
            await asyncio.sleep(3)
            
            print("\n[步骤 5] 验证发布...")
            await publisher.page.goto("https://mp.toutiao.com/profile_v4/graphic/articles")
            await asyncio.sleep(3)
            
            # 查找文章
            try:
                article_link = await publisher.page.query_selector(f'a:has-text("{test_title[:20]}")')
                if article_link:
                    print("✅ 验证成功：文章已出现在内容列表中！")
                    print("🎉 全自动发布成功！")
                else:
                    print("⚠️  未在列表中找到文章，可能还在审核中")
            except Exception as e:
                print(f"⚠️  验证失败: {e}")
        
        print("\n⏸️  浏览器保持打开，请检查结果")
        print("   按回车关闭...")
        input()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏸️  按回车关闭...")
        input()
    finally:
        await publisher.close()
        print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_full_auto_publish())
