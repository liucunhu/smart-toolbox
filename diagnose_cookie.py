"""
检查Cookie状态和登录诊断
"""
import asyncio
import json
from playwright.async_api import async_playwright
from app.db.session import SessionLocal
from app.models import Account


async def diagnose_login_status():
    """诊断登录状态"""
    
    print("="*80)
    print(" 头条登录状态诊断")
    print("="*80)
    
    # 从数据库获取账号
    db = SessionLocal()
    try:
        account = db.query(Account).filter(Account.id == 1).first()
        
        if not account:
            print("❌ 账号不存在")
            return
        
        print(f"\n📋 账号信息:")
        print(f"  ID: {account.id}")
        print(f"  用户名: {account.username}")
        print(f"  平台: {account.platform}")
        print(f"  有Cookie: {'是' if account.cookies else '否'}")
        
        if account.cookies:
            try:
                cookies = json.loads(account.cookies)
                print(f"  Cookie数量: {len(cookies)}")
                
                # 检查关键Cookie
                session_cookies = [c for c in cookies if 'session' in c.get('name', '').lower()]
                token_cookies = [c for c in cookies if 'token' in c.get('name', '').lower()]
                
                print(f"  Session Cookie: {len(session_cookies)} 个")
                print(f"  Token Cookie: {len(token_cookies)} 个")
                
                if session_cookies:
                    print(f"\n  关键Cookie示例:")
                    for cookie in session_cookies[:3]:
                        name = cookie.get('name')
                        domain = cookie.get('domain')
                        expires = cookie.get('expires')
                        print(f"    - {name}: domain={domain}, expires={expires}")
                
            except Exception as e:
                print(f"  ⚠️  Cookie解析失败: {e}")
        
    finally:
        db.close()
    
    print("\n" + "="*80)
    print("🧪 开始浏览器测试...")
    print("="*80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()
    
    try:
        # 步骤 1: 尝试使用Cookie
        if account.cookies:
            print("\n[步骤 1] 加载Cookie...")
            cookie_list = json.loads(account.cookies)
            await context.add_cookies(cookie_list)
            print(f"✅ 已加载 {len(cookie_list)} 个Cookie")
            
            # 访问头条首页
            print("\n[步骤 2] 访问头条首页...")
            await page.goto("https://mp.toutiao.com/", timeout=15000, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            current_url = page.url
            print(f"当前URL: {current_url}")
            
            if "profile" in current_url and "login" not in current_url:
                print("✅ Cookie登录成功！")
                
                # 保存新的Cookie
                new_cookies = await context.cookies()
                print(f"✅ 当前有 {len(new_cookies)} 个Cookie")
                
                # 更新数据库
                db = SessionLocal()
                try:
                    db_account = db.query(Account).filter(Account.id == 1).first()
                    if db_account:
                        db_account.cookies = json.dumps(new_cookies)
                        db.commit()
                        print("✅ Cookie已更新到数据库")
                finally:
                    db.close()
                
            else:
                print("❌ Cookie已失效，被重定向到登录页")
                print(f"重定向URL: {current_url}")
                
                print("\n💡 解决方案:")
                print("  1. 在打开的浏览器中手动完成登录")
                print("  2. 登录成功后按回车")
                print("  3. 系统将保存新的Cookie")
                
                input("\n请在浏览器中完成登录，然后按回车...")
                
                # 等待登录成功
                print("\n⌛ 等待登录成功...")
                for i in range(60):
                    await asyncio.sleep(2)
                    current_url = page.url
                    
                    if "profile" in current_url and "login" not in current_url:
                        print("✅ 检测到登录成功！")
                        break
                    
                    if i % 10 == 0:
                        print(f"  等待中... ({i+1}/60)")
                
                # 保存新Cookie
                new_cookies = await context.cookies()
                print(f"\n✅ 已获取 {len(new_cookies)} 个新Cookie")
                
                db = SessionLocal()
                try:
                    db_account = db.query(Account).filter(Account.id == 1).first()
                    if db_account:
                        db_account.cookies = json.dumps(new_cookies)
                        db.commit()
                        print("✅ 新Cookie已保存到数据库")
                finally:
                    db.close()
        
        print("\n⌛ 浏览器保持打开，按回车关闭...")
        input()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⌛ 按回车关闭...")
        input()
    finally:
        await browser.close()
        await playwright.stop()
        print("\n✅ 诊断完成")


if __name__ == "__main__":
    asyncio.run(diagnose_login_status())
