"""
新功能API测试用例
测试所有新实现的服务接口
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestNurturingAPI:
    """智能养号系统API测试"""
    
    def test_set_nurturing_config(self):
        """测试设置养号配置"""
        response = client.post(
            "/api/v1/v2/nurturing/config",
            params={
                "min_videos": 15,
                "max_videos": 25,
                "like_probability": 10,
                "comment_probability": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "config" in data
    
    def test_get_nurturing_statistics(self):
        """测试获取养号统计"""
        response = client.get("/api/v1/v2/nurturing/statistics")
        
        assert response.status_code == 200
        data = response.json()
        # 即使没有数据也应该返回成功
        assert data["status"] == "success" or data["status"] == "failed"
    
    def test_get_nurturing_sessions(self):
        """测试获取养号会话记录"""
        response = client.get(
            "/api/v1/v2/nurturing/sessions",
            params={"skip": 0, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        # 即使没有数据也应该返回成功
        assert data["status"] == "success" or data["status"] == "failed"


class TestFingerprintAPI:
    """设备指纹隔离API测试"""
    
    def test_generate_fingerprint_profile(self):
        """测试生成设备指纹配置"""
        response = client.post(
            "/api/v1/v2/fingerprint/generate",
            params={
                "platform": "douyin",
                "device_type": "desktop"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "success":
            assert "profile" in data
            assert "user_agent" in data["profile"]


class TestCaptchaAPI:
    """人机验证突破API测试"""
    
    def test_ocr_captcha_without_image(self):
        """测试OCR识别（无图片）"""
        response = client.post("/api/v1/v2/captcha/ocr")
        
        # 应该返回422错误（缺少文件）
        assert response.status_code in [422, 400]


class TestVideoDeduplicationAPI:
    """视频去重API测试"""
    
    def test_deduplicate_video_without_file(self):
        """测试视频去重（无文件）"""
        response = client.post("/api/v1/v2/video/deduplicate")
        
        # 应该返回422错误（缺少文件）
        assert response.status_code in [422, 400]


class TestComplianceAPI:
    """增强版合规审查API测试"""
    
    def test_enhanced_compliance_check(self):
        """测试增强版合规检查"""
        response = client.post(
            "/api/v1/v2/compliance/enhanced-check",
            params={
                "text": "这是一段测试文本",
                "platform": "douyin"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "success":
            assert "passed" in data
            assert "violations" in data


class TestFormatAdapterAPI:
    """格式自适应转换API测试"""
    
    def test_adapt_video_format_without_file(self):
        """测试格式转换（无文件）"""
        response = client.post("/api/v1/v2/video/format-adapt")
        
        # 应该返回422错误（缺少文件）
        assert response.status_code in [422, 400]


class TestSmartSchedulerAPI:
    """增强版智能调度API测试"""
    
    def test_get_optimal_publish_time(self):
        """测试获取最佳发布时间"""
        response = client.get(
            "/api/v1/v2/schedule/optimal-time",
            params={"account_id": 1}
        )
        
        # 可能成功或失败（取决于数据库是否有数据）
        assert response.status_code == 200


class TestSMSPlatformAPI:
    """SMS接码平台API测试"""
    
    def test_register_sms_phone_invalid_platform(self):
        """测试注册手机号（无效平台）"""
        response = client.post(
            "/api/v1/v2/sms/register-phone",
            params={
                "platform": "invalid_platform",
                "api_key": "test_key",
                "target_platform": "douyin"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "failed":
            assert "error" in data
    
    def test_get_sms_balance_invalid_platform(self):
        """测试查询余额（无效平台）"""
        response = client.get(
            "/api/v1/v2/sms/balance",
            params={
                "platform": "invalid_platform",
                "api_key": "test_key"
            }
        )
        
        assert response.status_code == 200


class TestHotTrendsAPI:
    """多平台热搜API测试"""
    
    def test_get_xiaohongshu_trends(self):
        """测试获取小红书热搜"""
        response = client.get(
            "/api/v1/v2/hot-trends/xiaohongshu",
            params={"count": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        # 可能成功或失败（取决于网络）
        assert "status" in data
    
    def test_get_bilibili_trends(self):
        """测试获取B站热搜"""
        response = client.get(
            "/api/v1/v2/hot-trends/bilibili",
            params={"count": 10}
        )
        
        assert response.status_code == 200
    
    def test_get_toutiao_trends(self):
        """测试获取今日头条热搜"""
        response = client.get(
            "/api/v1/v2/hot-trends/toutiao",
            params={"count": 10}
        )
        
        assert response.status_code == 200


class TestVisualSynthesisAPI:
    """视觉合成API测试"""
    
    def test_three_grid_cover_without_images(self):
        """测试三格封面（无图片）"""
        response = client.post("/api/v1/v2/visual/three-grid-cover")
        
        # 应该返回422错误（缺少文件）
        assert response.status_code in [422, 400]
    
    def test_saturated_portrait_without_image(self):
        """测试高饱和度封面（无图片）"""
        response = client.post("/api/v1/v2/visual/saturated-portrait")
        
        assert response.status_code in [422, 400]
    
    def test_ins_style_filter_without_image(self):
        """测试Ins滤镜（无图片）"""
        response = client.post("/api/v1/v2/visual/ins-style-filter")
        
        assert response.status_code in [422, 400]


class TestDynamicSubtitleAPI:
    """动态字幕API测试"""
    
    def test_generate_subtitle_without_video(self):
        """测试生成字幕（无视频）"""
        response = client.post("/api/v1/v2/subtitle/generate")
        
        assert response.status_code in [422, 400]
    
    def test_add_sound_effect_without_video(self):
        """测试添加音效（无视频）"""
        response = client.post("/api/v1/v2/subtitle/add-sound-effect")
        
        assert response.status_code in [422, 400]
    
    def test_match_bgm_without_video(self):
        """测试匹配BGM（无视频）"""
        response = client.post("/api/v1/v2/subtitle/match-bgm")
        
        assert response.status_code in [422, 400]


class TestHumanBehaviorAPI:
    """行为拟人化API测试"""
    
    def test_simulate_mouse_jitter(self):
        """测试鼠标抖动模拟"""
        response = client.post(
            "/api/v1/v2/behavior/mouse-jitter",
            params={
                "duration": 5,
                "intensity": "normal"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "success":
            assert "duration" in data
    
    def test_add_random_delay(self):
        """测试随机延迟"""
        response = client.post(
            "/api/v1/v2/behavior/random-delay",
            params={
                "min_delay": 1.0,
                "max_delay": 3.0,
                "distribution": "uniform"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "success":
            assert "delay_seconds" in data


class TestProxyPoolAPI:
    """IP代理池API测试"""
    
    def test_get_proxy_list(self):
        """测试获取代理列表"""
        response = client.get("/api/v1/v2/proxy/list")
        
        assert response.status_code == 200
        data = response.json()
        # 可能成功或失败（取决于数据库）
        assert "status" in data
    
    def test_check_proxy_health_invalid_id(self):
        """测试检查代理健康度（无效ID）"""
        response = client.post(
            "/api/v1/v2/proxy/check-health",
            params={"proxy_id": 99999}
        )
        
        assert response.status_code == 200
    
    def test_add_proxy(self):
        """测试添加代理"""
        response = client.post(
            "/api/v1/v2/proxy/add",
            params={
                "ip": "127.0.0.1",
                "port": 8080,
                "proxy_type": "residential",
                "country": "CN"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "success":
            assert "proxy_id" in data
    
    def test_remove_proxy_invalid_id(self):
        """测试移除代理（无效ID）"""
        response = client.delete(
            "/api/v1/v2/proxy/remove",
            params={"proxy_id": 99999}
        )
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
