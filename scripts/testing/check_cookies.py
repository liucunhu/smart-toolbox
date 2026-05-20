"""检查头条账号的Cookie状态"""
from app.db.session import SessionLocal
from app.models import Account

db = SessionLocal()
accounts = db.query(Account).filter(Account.platform == 'toutiao').all()

print(f"找到 {len(accounts)} 个头条账号:\n")
for acc in accounts:
    print(f'ID: {acc.id}')
    print(f'Username: {acc.username}')
    print(f'Has cookies: {bool(acc.cookies)}')
    print(f'Cookie length: {len(acc.cookies) if acc.cookies else 0}')
    print(f'Status: {acc.status}')
    print('---')

db.close()
