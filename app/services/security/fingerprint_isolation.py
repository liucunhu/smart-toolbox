"""
设备指纹隔离服务
实现Canvas指纹、WebGL指纹、User-Agent随机化等反指纹识别技术
"""
import random
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from playwright.async_api import BrowserContext

logger = logging.getLogger(__name__)


@dataclass
class DeviceProfile:
    """设备配置文件"""
    # User-Agent
    user_agent: str
    
    # 屏幕信息
    screen_width: int
    screen_height: int
    screen_color_depth: int
    screen_pixel_depth: int
    
    # 时区信息
    timezone: str
    timezone_offset: int
    
    # 语言信息
    language: str
    languages: List[str]
    
    # 平台信息
    platform: str
    vendor: str
    product: str
    
    # WebGL信息
    webgl_vendor: str
    webgl_renderer: str
    
    # Canvas指纹
    canvas_noise: float
    
    # 字体列表
    fonts: List[str]
    
    # 媒体设备
    media_devices: List[str]
    
    # 硬件信息
    hardware_concurrency: int
    device_memory: int
    
    # 网络信息
    connection_type: str
    effective_type: str
    
    # 电池信息
    battery_level: float


class FingerprintIsolationEngine:
    """设备指纹隔离引擎"""
    
    # 常见User-Agent池
    USER_AGENTS = [
        # Windows Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        
        # Mac Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Windows Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        
        # Mac Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    ]
    
    # WebGL厂商和渲染器池
    WEBGL_VENDORS = [
        "Google Inc. (NVIDIA)",
        "Google Inc. (Intel)",
        "Google Inc. (AMD)",
        "Intel Inc.",
        "NVIDIA Corporation",
        "ATI Technologies Inc."
    ]
    
    WEBGL_RENDERERS = [
        "ANGLE (NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0)",
        "Intel(R) UHD Graphics 630",
        "NVIDIA GeForce GTX 1650/PCIe/SSE2",
        "AMD Radeon RX 580 Series"
    ]
    
    # 常见字体列表
    COMMON_FONTS = [
        "Arial", "Arial Black", "Arial Narrow", "Calibri", "Cambria",
        "Cambria Math", "Comic Sans MS", "Consolas", "Courier", "Courier New",
        "Georgia", "Helvetica", "Impact", "Lucida Console", "Lucida Sans Unicode",
        "Microsoft Sans Serif", "Palatino Linotype", "Segoe UI", "Tahoma",
        "Times", "Times New Roman", "Trebuchet MS", "Verdana", "Monaco",
        "Menlo", "Ubuntu", "Roboto", "Open Sans", "Lato", "Oswald", "Source Sans Pro"
    ]
    
    # 时区列表
    TIMEZONES = [
        "Asia/Shanghai", "Asia/Beijing", "Asia/Hong_Kong", "Asia/Tokyo",
        "America/New_York", "America/Los_Angeles", "America/Chicago",
        "Europe/London", "Europe/Paris", "Europe/Berlin", "Australia/Sydney"
    ]
    
    # 语言列表
    LANGUAGES = [
        ["zh-CN", "zh", "en"],
        ["zh-TW", "zh", "en"],
        ["en-US", "en"],
        ["en-GB", "en"],
        ["ja-JP", "ja", "en"]
    ]
    
    def __init__(self):
        self.profiles_cache: Dict[str, DeviceProfile] = {}
    
    def _generate_random_user_agent(self) -> str:
        """
        生成随机User-Agent
        
        Returns:
            str: User-Agent字符串
        """
        return random.choice(self.USER_AGENTS)
    
    def _generate_random_screen_size(self) -> tuple:
        """
        生成随机屏幕尺寸
        
        Returns:
            tuple: (width, height)
        """
        # 常见分辨率
        resolutions = [
            (1920, 1080), (1920, 1200), (2560, 1440), (3840, 2160),
            (1366, 768), (1536, 864), (1440, 900), (1680, 1050)
        ]
        return random.choice(resolutions)
    
    def _generate_random_timezone(self) -> tuple:
        """
        生成随机时区信息
        
        Returns:
            tuple: (timezone, offset)
        """
        timezone = random.choice(self.TIMEZONES)
        # 生成-12到+12的时区偏移
        offset = random.randint(-12, 12)
        return timezone, offset
    
    def _generate_random_language(self) -> tuple:
        """
        生成随机语言信息
        
        Returns:
            tuple: (language, languages_list)
        """
        languages_list = random.choice(self.LANGUAGES)
        return languages_list[0], languages_list
    
    def _generate_random_webgl_info(self) -> tuple:
        """
        生成随机WebGL信息
        
        Returns:
            tuple: (vendor, renderer)
        """
        vendor = random.choice(self.WEBGL_VENDORS)
        renderer = random.choice(self.WEBGL_RENDERERS)
        return vendor, renderer
    
    def _generate_random_fonts(self, min_count: int = 10, max_count: int = 20) -> List[str]:
        """
        生成随机字体列表
        
        Args:
            min_count: 最少字体数量
            max_count: 最多字体数量
            
        Returns:
            List[str]: 字体列表
        """
        count = random.randint(min_count, max_count)
        return random.sample(self.COMMON_FONTS, min(count, len(self.COMMON_FONTS)))
    
    def _generate_canvas_noise(self) -> float:
        """
        生成Canvas噪声值
        
        Returns:
            float: 噪声值（0-1之间）
        """
        return random.uniform(0.001, 0.01)
    
    def _generate_hardware_info(self) -> tuple:
        """
        生成随机硬件信息
        
        Returns:
            tuple: (concurrency, memory)
        """
        concurrency = random.choice([2, 4, 6, 8, 12, 16])
        memory = random.choice([4, 8, 16, 32])
        return concurrency, memory
    
    def _generate_network_info(self) -> tuple:
        """
        生成随机网络信息
        
        Returns:
            tuple: (connection_type, effective_type)
        """
        connection_type = random.choice(["wifi", "cellular", "ethernet"])
        effective_type = random.choice(["4g", "3g", "2g", "slow-2g"])
        return connection_type, effective_type
    
    def _generate_media_devices(self) -> List[str]:
        """
        生成随机媒体设备列表
        
        Returns:
            List[str]: 媒体设备列表
        """
        devices = [
            {"deviceId": "default", "kind": "audioinput", "label": "默认 - 麦克风 (Realtek Audio)", "groupId": "default"},
            {"deviceId": "communications", "kind": "audioinput", "label": "通信 - 麦克风 (Realtek Audio)", "groupId": "default"},
            {"deviceId": "default", "kind": "audiooutput", "label": "默认 - 扬声器 (Realtek Audio)", "groupId": "default"},
        ]
        
        # 随机添加摄像头
        if random.random() < 0.8:  # 80%概率有摄像头
            camera_label = random.choice([
                "Integrated Camera",
                "HD WebCam",
                "FaceTime HD Camera",
                "USB2.0 Camera"
            ])
            devices.append({
                "deviceId": f"camera_{random.randint(1000, 9999)}",
                "kind": "videoinput",
                "label": camera_label,
                "groupId": "camera_group"
            })
        
        return devices
    
    def generate_device_profile(self, account_id: Optional[str] = None) -> DeviceProfile:
        """
        生成设备配置文件
        
        Args:
            account_id: 账号ID（用于缓存）
            
        Returns:
            DeviceProfile: 设备配置文件
        """
        # 如果有缓存，直接返回
        if account_id and account_id in self.profiles_cache:
            return self.profiles_cache[account_id]
        
        # 生成屏幕信息
        screen_width, screen_height = self._generate_random_screen_size()
        
        # 生成时区信息
        timezone, timezone_offset = self._generate_random_timezone()
        
        # 生成语言信息
        language, languages = self._generate_random_language()
        
        # 生成WebGL信息
        webgl_vendor, webgl_renderer = self._generate_random_webgl_info()
        
        # 生成硬件信息
        hardware_concurrency, device_memory = self._generate_hardware_info()
        
        # 生成网络信息
        connection_type, effective_type = self._generate_network_info()
        
        # 创建设备配置
        profile = DeviceProfile(
            user_agent=self._generate_random_user_agent(),
            screen_width=screen_width,
            screen_height=screen_height,
            screen_color_depth=24,
            screen_pixel_depth=24,
            timezone=timezone,
            timezone_offset=timezone_offset,
            language=language,
            languages=languages,
            platform=random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            vendor=random.choice(["Google Inc.", "Apple Computer, Inc."]),
            product="Gecko",
            webgl_vendor=webgl_vendor,
            webgl_renderer=webgl_renderer,
            canvas_noise=self._generate_canvas_noise(),
            fonts=self._generate_random_fonts(),
            media_devices=self._generate_media_devices(),
            hardware_concurrency=hardware_concurrency,
            device_memory=device_memory,
            connection_type=connection_type,
            effective_type=effective_type,
            battery_level=random.uniform(0.2, 1.0)
        )
        
        # 缓存配置
        if account_id:
            self.profiles_cache[account_id] = profile
        
        logger.info(f"✅ 生成设备配置文件: {profile.user_agent[:50]}...")
        return profile
    
    async def apply_fingerprint_isolation(
        self,
        context: BrowserContext,
        profile: DeviceProfile
    ):
        """
        应用设备指纹隔离到浏览器上下文
        
        Args:
            context: Playwright浏览器上下文
            profile: 设备配置文件
        """
        try:
            # 设置User-Agent
            await context.set_extra_http_headers({
                "User-Agent": profile.user_agent
            })
            
            # 注入JavaScript代码以覆盖浏览器指纹
            await context.add_init_script(f"""
                // 覆盖Navigator对象
                Object.defineProperty(navigator, 'userAgent', {{
                    get: () => '{profile.user_agent}'
                }});
                
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{profile.platform}'
                }});
                
                Object.defineProperty(navigator, 'vendor', {{
                    get: () => '{profile.vendor}'
                }});
                
                Object.defineProperty(navigator, 'product', {{
                    get: () => '{profile.product}'
                }});
                
                Object.defineProperty(navigator, 'language', {{
                    get: () => '{profile.language}'
                }});
                
                Object.defineProperty(navigator, 'languages', {{
                    get: () => {json.dumps(profile.languages)}
                }});
                
                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: () => {profile.hardware_concurrency}
                }});
                
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {profile.device_memory}
                }});
                
                // 覆盖Screen对象
                Object.defineProperty(screen, 'width', {{
                    get: () => {profile.screen_width}
                }});
                
                Object.defineProperty(screen, 'height', {{
                    get: () => {profile.screen_height}
                }});
                
                Object.defineProperty(screen, 'colorDepth', {{
                    get: () => {profile.screen_color_depth}
                }});
                
                Object.defineProperty(screen, 'pixelDepth', {{
                    get: () => {profile.screen_pixel_depth}
                }});
                
                // 覆盖时区
                const originalTimezoneOffset = Date.prototype.getTimezoneOffset;
                Date.prototype.getTimezoneOffset = function() {{
                    return {profile.timezone_offset * 60};
                }};
                
                // 覆盖WebGL指纹
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                        return '{profile.webgl_vendor}';
                    }}
                    if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                        return '{profile.webgl_renderer}';
                    }}
                    return getParameter.call(this, parameter);
                }};
                
                // 覆盖Canvas指纹（添加噪声）
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {{
                    const context = this.getContext('2d');
                    if (context) {{
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        const data = imageData.data;
                        // 添加微小噪声
                        const noise = {profile.canvas_noise};
                        for (let i = 0; i < data.length; i += 4) {{
                            if (Math.random() < noise) {{
                                data[i] = Math.min(255, data[i] + (Math.random() - 0.5) * 2);
                                data[i + 1] = Math.min(255, data[i + 1] + (Math.random() - 0.5) * 2);
                                data[i + 2] = Math.min(255, data[i + 2] + (Math.random() - 0.5) * 2);
                            }}
                        }}
                        context.putImageData(imageData, 0, 0);
                    }}
                    return originalToDataURL.apply(this, arguments);
                }};
                
                // 覆盖字体检测
                const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
                CanvasRenderingContext2D.prototype.measureText = function(text) {{
                    const result = originalMeasureText.call(this, text);
                    // 添加微小随机偏移
                    result.width += (Math.random() - 0.5) * 0.01;
                    return result;
                }};
                
                // 覆盖媒体设备枚举
                const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                navigator.mediaDevices.enumerateDevices = async function() {{
                    const fakeDevices = {json.dumps(profile.media_devices)};
                    return fakeDevices.map(device => ({{
                        deviceId: device.deviceId,
                        kind: device.kind,
                        label: device.label,
                        groupId: device.groupId
                    }}));
                }};
                
                // 覆盖网络信息
                Object.defineProperty(navigator.connection, 'type', {{
                    get: () => '{profile.connection_type}'
                }});
                
                Object.defineProperty(navigator.connection, 'effectiveType', {{
                    get: () => '{profile.effective_type}'
                }});
                
                // 覆盖电池API
                if (navigator.getBattery) {{
                    const originalGetBattery = navigator.getBattery;
                    navigator.getBattery = async function() {{
                        return {{
                            charging: Math.random() > 0.5,
                            chargingTime: Infinity,
                            dischargingTime: Infinity,
                            level: {profile.battery_level},
                            addEventListener: () => {{}},
                            removeEventListener: () => {{}}
                        }};
                    }};
                }}
                
                console.log('✅ 设备指纹隔离已应用');
            """)
            
            # 设置视口大小
            await context.set_viewport_size({
                "width": profile.screen_width,
                "height": profile.screen_height
            })
            
            logger.info("✅ 设备指纹隔离已应用到浏览器上下文")
            
        except Exception as e:
            logger.error(f"应用设备指纹隔离失败: {e}")
            raise
    
    def get_fingerprint_hash(self, profile: DeviceProfile) -> str:
        """
        获取设备指纹哈希值
        
        Args:
            profile: 设备配置文件
            
        Returns:
            str: 指纹哈希
        """
        import hashlib
        
        # 将配置转换为字典
        profile_dict = asdict(profile)
        
        # 移除某些字段（如battery_level等会变化的）
        profile_dict.pop('battery_level', None)
        
        # 生成哈希
        profile_json = json.dumps(profile_dict, sort_keys=True)
        return hashlib.md5(profile_json.encode()).hexdigest()
    
    def validate_profile_consistency(self, profile: DeviceProfile) -> bool:
        """
        验证设备配置文件的一致性
        
        Args:
            profile: 设备配置文件
            
        Returns:
            bool: 是否一致
        """
        try:
            # 检查屏幕尺寸是否合理
            if profile.screen_width < 800 or profile.screen_width > 7680:
                return False
            if profile.screen_height < 600 or profile.screen_height > 4320:
                return False
            
            # 检查硬件并发数
            if profile.hardware_concurrency < 1 or profile.hardware_concurrency > 64:
                return False
            
            # 检查内存
            if profile.device_memory < 2 or profile.device_memory > 128:
                return False
            
            # 检查电池电量
            if profile.battery_level < 0 or profile.battery_level > 1:
                return False
            
            # 检查时区偏移
            if abs(profile.timezone_offset) > 14:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证设备配置失败: {e}")
            return False
    
    def export_profile(self, profile: DeviceProfile, filepath: str):
        """
        导出设备配置文件
        
        Args:
            profile: 设备配置文件
            filepath: 导出文件路径
        """
        profile_dict = asdict(profile)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile_dict, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 设备配置已导出到: {filepath}")
    
    def import_profile(self, filepath: str) -> DeviceProfile:
        """
        导入设备配置文件
        
        Args:
            filepath: 导入文件路径
            
        Returns:
            DeviceProfile: 设备配置文件
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            profile_dict = json.load(f)
        profile = DeviceProfile(**profile_dict)
        logger.info(f"✅ 设备配置已从 {filepath} 导入")
        return profile


# 创建全局指纹隔离引擎实例
_fingerprint_engine = None


def get_fingerprint_engine() -> FingerprintIsolationEngine:
    """
    获取指纹隔离引擎实例（单例模式）
    
    Returns:
        FingerprintIsolationEngine: 指纹隔离引擎实例
    """
    global _fingerprint_engine
    if _fingerprint_engine is None:
        _fingerprint_engine = FingerprintIsolationEngine()
    return _fingerprint_engine
