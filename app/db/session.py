from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from app.core.config import settings

# 创建 Base 类
Base = declarative_base()

# 增加连接池配置，提高并发性能
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 使用 scoped_session 确保线程安全
db_session = scoped_session(SessionLocal)

def get_db():
    """FastAPI 依赖注入函数"""
    db = db_session()
    try:
        yield db
    finally:
        db_session.remove()
