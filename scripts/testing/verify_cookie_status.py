"""验证头条账号Cookie状态"""
from app.db.session import SessionLocal
from app.models import Account
import json

db = SessionLocal()

accounts = db.query(Account).filter(Account.platform == 'toutiao').all()

print(f"找到 {len(accounts)} 个头条账号:\n")
for acc in accounts:
    print(f"ID: {acc.id}")
    print(f"Username: {acc.username}")
    print(f"Status: {acc.status}")
    print(f"Has cookies: {bool(acc.cookies)}")
    
    if acc.cookies:
        try:
            cookie_list = json.loads(acc.cookies)
            print(f"Cookie count: {len(cookie_list)}")
            # 显示几个关键的cookie
            important_cookies = [c for c in cookie_list if c.get('name') in ['sessionid', 'tt_webid', 'passport_csrf_token']]
            print(f"Important cookies: {len(important_cookies)}")
            for c in important_cookies:
                print(f"  - {c['name']}: {c['value'][:20]}...")
        except Exception as e:
            print(f"Cookie parse error: {e}")
    else:
        print("No cookies saved!")
    
    print("-" * 50)

db.close()
