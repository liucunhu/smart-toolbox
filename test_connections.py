import pymysql
import redis
import sys

def test_mysql():
    print("🔍 正在测试 MySQL 连接...")
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='toolbox_user',
            password='ToolboxPass123',
            database='smart_toolbox',
            charset='utf8mb4'
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL 连接成功! 版本: {version[0]}")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ MySQL 连接失败: {e}")
        return False

def test_redis():
    print("🔍 正在测试 Redis 连接...")
    try:
        r = redis.Redis(
            host='localhost',
            port=6379,
            password='RedisPass123',
            decode_responses=True
        )
        r.set('connection_test', 'Smart-Toolbox-Ready')
        val = r.get('connection_test')
        if val == 'Smart-Toolbox-Ready':
            print("✅ Redis 连接成功! 读写测试通过。")
            return True
        else:
            print("❌ Redis 读写数据不一致")
            return False
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False

if __name__ == "__main__":
    print("="*30)
    print("   Smart-Toolbox 环境检测")
    print("="*30)
    
    mysql_ok = test_mysql()
    redis_ok = test_redis()
    
    print("="*30)
    if mysql_ok and redis_ok:
        print("🎉 所有基础服务就绪，可以启动后端！")
    else:
        print("⚠️ 请检查 Docker 容器状态或网络配置。")
    print("="*30)
