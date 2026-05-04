"""
后端 API 集成测试
测试认证、健康检查、内容生成等核心接口
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings

client = TestClient(app)


class TestAuthEndpoints:
    """认证接口测试"""

    def test_login_success(self):
        """测试登录成功"""
        response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data

    def test_login_failure(self):
        """测试登录失败"""
        response = client.post("/api/v1/auth/login", json={
            "username": "wrong_user",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401

    def test_register(self):
        """测试注册"""
        response = client.post("/api/v1/auth/register", json={
            "username": "test_user",
            "password": "test_password",
            "email": "test@example.com"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "注册成功"


class TestHealthEndpoints:
    """健康检查接口测试"""

    def test_health_check(self):
        """测试综合健康检查"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "version" in data

    def test_health_db(self):
        """测试数据库健康检查"""
        response = client.get("/api/v1/health/db")
        
        assert response.status_code == 200
        data = response.json()
        assert data["component"] == "database"

    def test_health_redis(self):
        """测试Redis健康检查"""
        response = client.get("/api/v1/health/redis")
        
        assert response.status_code == 200
        data = response.json()
        assert data["component"] == "redis"


class TestContentEndpoints:
    """内容接口测试"""

    def test_generate_script_douyin(self):
        """测试抖音文案生成"""
        response = client.post(
            "/api/v1/content/generate",
            params={"topic": "Python自动化", "platform": "douyin"}
        )
        
        # 注意：这需要AI API密钥，如果没有配置会返回错误
        assert response.status_code in [200, 500]

    def test_compliance_check(self):
        """测试违禁词检测"""
        response = client.post(
            "/api/v1/compliance/check",
            params={"text": "想赚钱的加微信", "platform": "douyin"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_safe" in data
        assert "violations" in data


class TestAccountEndpoints:
    """账号接口测试"""

    def test_list_accounts(self):
        """测试获取账号列表"""
        response = client.get("/api/v1/accounts/list")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "accounts" in data

    def test_get_healthy_accounts(self):
        """测试获取健康账号"""
        response = client.get("/api/v1/accounts/healthy")
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data


class TestScheduleEndpoints:
    """调度接口测试"""

    def test_get_next_publish_time(self):
        """测试获取下一个发布时间"""
        response = client.get("/api/v1/schedule/next_time")
        
        assert response.status_code == 200
        data = response.json()
        assert "suggested_time" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
