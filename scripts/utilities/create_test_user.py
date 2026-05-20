"""
创建测试账号脚本
"""
from app.db.session import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    """创建测试用户"""
    db = SessionLocal()
    
    try:
        # 检查是否已存在
        existing_user = db.query(User).filter(
            (User.username == 'testadmin') | (User.email == 'test@smart-toolbox.com')
        ).first()
        
        if existing_user:
            print(f"⚠️  测试账号已存在: {existing_user.username}")
            return
        
        # 创建新用户
        hashed_password = pwd_context.hash("Test@123456")
        
        test_user = User(
            username='testadmin',
            email='test@smart-toolbox.com',
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("✅ 测试账号创建成功！")
        print("=" * 50)
        print("📋 登录信息:")
        print(f"   用户名: testadmin")
        print(f"   密码: Test@123456")
        print(f"   邮箱: test@smart-toolbox.com")
        print("=" * 50)
        print("\n💡 提示: 请访问 http://localhost:3003 登录")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
