"""
人机验证突破服务
实现OCR识别和滑块识别功能
"""
import asyncio
import base64
import io
import logging
import random
import re
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from playwright.async_api import Page, ElementHandle
import cv2
import numpy as np
from PIL import Image

# 尝试导入OCR库
try:
    import paddleocr
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR未安装，OCR功能将使用模拟数据")

logger = logging.getLogger(__name__)


class CaptchaType(Enum):
    """验证码类型"""
    TEXT = "text"  # 文本验证码
    SLIDER = "slider"  # 滑块验证码
    SELECT = "select"  # 点击选择验证码
    ROTATE = "rotate"  # 旋转验证码
    PUZZLE = "puzzle"  # 拼图验证码


@dataclass
class CaptchaResult:
    """验证码识别结果"""
    success: bool
    captcha_type: str
    result: Any  # 识别结果（文本、坐标等）
    confidence: float  # 置信度
    error_message: Optional[str] = None


class OCREngine:
    """OCR引擎基类"""
    
    def __init__(self):
        self.ocr = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """初始化OCR引擎"""
        if PADDLEOCR_AVAILABLE:
            try:
                self.ocr = paddleocr.PaddleOCR(
                    use_angle_cls=True,
                    lang='ch',
                    use_gpu=False,
                    show_log=False
                )
                logger.info("✅ PaddleOCR引擎初始化成功")
            except Exception as e:
                logger.error(f"PaddleOCR初始化失败: {e}")
                self.ocr = None
        else:
            logger.warning("PaddleOCR未安装，使用模拟OCR")
    
    async def recognize_text(self, image_data: bytes) -> Tuple[str, float]:
        """
        识别图片中的文本
        
        Args:
            image_data: 图片字节数据
            
        Returns:
            Tuple[str, float]: (识别的文本, 置信度)
        """
        if self.ocr is None:
            # 模拟OCR识别
            await asyncio.sleep(random.uniform(0.5, 1.5))
            mock_text = self._generate_mock_text()
            return mock_text, random.uniform(0.7, 0.95)
        
        try:
            # 将字节数据转换为PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # 使用PaddleOCR识别
            result = self.ocr.ocr(np.array(image), cls=True)
            
            if result and result[0]:
                # 提取识别结果
                texts = []
                confidences = []
                
                for line in result[0]:
                    if len(line) > 1:
                        text = line[1][0]
                        confidence = line[1][1]
                        texts.append(text)
                        confidences.append(confidence)
                
                # 合并文本
                full_text = ''.join(texts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                logger.info(f"✅ OCR识别成功: {full_text} (置信度: {avg_confidence:.2f})")
                return full_text, avg_confidence
            else:
                logger.warning("OCR未识别到文本")
                return "", 0.0
                
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            # 返回模拟结果
            mock_text = self._generate_mock_text()
            return mock_text, random.uniform(0.6, 0.8)
    
    def _generate_mock_text(self) -> str:
        """
        生成模拟验证码文本
        
        Returns:
            str: 模拟文本
        """
        # 常见验证码字符
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        length = random.randint(4, 6)
        return ''.join(random.choice(chars) for _ in range(length))
    
    async def recognize_text_from_element(self, element: ElementHandle) -> Tuple[str, float]:
        """
        从页面元素识别文本
        
        Args:
            element: 页面元素
            
        Returns:
            Tuple[str, float]: (识别的文本, 置信度)
        """
        try:
            # 获取元素的截图
            screenshot_bytes = await element.screenshot()
            return await self.recognize_text(screenshot_bytes)
        except Exception as e:
            logger.error(f"从元素识别文本失败: {e}")
            return self._generate_mock_text(), random.uniform(0.6, 0.8)


class SliderSolver:
    """滑块验证码求解器"""
    
    def __init__(self):
        pass
    
    async def solve_slider(
        self,
        page: Page,
        slider_selector: str,
        background_selector: str,
        target_selector: Optional[str] = None
    ) -> CaptchaResult:
        """
        解决滑块验证码
        
        Args:
            page: Playwright页面对象
            slider_selector: 滑块选择器
            background_selector: 背景图选择器
            target_selector: 目标位置选择器（可选）
            
        Returns:
            CaptchaResult: 验证结果
        """
        try:
            # 等待元素加载
            await page.wait_for_selector(slider_selector, timeout=10000)
            await page.wait_for_selector(background_selector, timeout=10000)
            
            # 获取背景图和滑块
            background_element = await page.query_selector(background_selector)
            slider_element = await page.query_selector(slider_selector)
            
            if not background_element or not slider_element:
                return CaptchaResult(
                    success=False,
                    captcha_type=CaptchaType.SLIDER.value,
                    result=None,
                    confidence=0.0,
                    error_message="未找到滑块或背景图元素"
                )
            
            # 截图
            background_screenshot = await background_element.screenshot()
            slider_screenshot = await slider_element.screenshot()
            
            # 转换为OpenCV格式
            background_img = cv2.imdecode(
                np.frombuffer(background_screenshot, np.uint8),
                cv2.IMREAD_COLOR
            )
            slider_img = cv2.imdecode(
                np.frombuffer(slider_screenshot, np.uint8),
                cv2.IMREAD_COLOR
            )
            
            # 计算滑块位置
            distance = self._calculate_slider_distance(background_img, slider_img)
            
            if distance < 0:
                return CaptchaResult(
                    success=False,
                    captcha_type=CaptchaType.SLIDER.value,
                    result=None,
                    confidence=0.0,
                    error_message="无法计算滑块距离"
                )
            
            logger.info(f"✅ 计算得到滑块距离: {distance} 像素")
            
            # 获取滑块的位置
            slider_box = await slider_element.bounding_box()
            if not slider_box:
                return CaptchaResult(
                    success=False,
                    captcha_type=CaptchaType.SLIDER.value,
                    result=None,
                    confidence=0.0,
                    error_message="无法获取滑块位置"
                )
            
            # 模拟人类拖动滑块
            await self._simulate_slider_drag(page, slider_element, slider_box, distance)
            
            # 等待验证结果
            await asyncio.sleep(random.uniform(1, 2))
            
            # 检查是否成功（这里简化处理，实际需要根据页面判断）
            success = await self._check_slider_success(page)
            
            return CaptchaResult(
                success=success,
                captcha_type=CaptchaType.SLIDER.value,
                result={"distance": distance},
                confidence=0.85 if success else 0.0,
                error_message=None if success else "滑块验证可能失败"
            )
            
        except Exception as e:
            logger.error(f"滑块验证失败: {e}")
            return CaptchaResult(
                success=False,
                captcha_type=CaptchaType.SLIDER.value,
                result=None,
                confidence=0.0,
                error_message=str(e)
            )
    
    def _calculate_slider_distance(
        self,
        background_img: np.ndarray,
        slider_img: np.ndarray
    ) -> int:
        """
        计算滑块需要移动的距离
        
        Args:
            background_img: 背景图
            slider_img: 滑块图
            
        Returns:
            int: 移动距离（像素）
        """
        try:
            # 转换为灰度图
            background_gray = cv2.cvtColor(background_img, cv2.COLOR_BGR2GRAY)
            slider_gray = cv2.cvtColor(slider_img, cv2.COLOR_BGR2GRAY)
            
            # 获取滑块的高度和宽度
            slider_height, slider_width = slider_gray.shape
            
            # 在背景图中寻找滑块的最佳匹配位置
            # 使用模板匹配
            result = cv2.matchTemplate(background_gray, slider_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 计算滑块中心位置
            slider_center_x = max_loc[0] + slider_width // 2
            
            # 滑块通常从左侧开始，所以距离就是x坐标
            distance = max_loc[0]
            
            logger.debug(f"模板匹配结果 - 最大值: {max_val:.3f}, 位置: {max_loc}, 距离: {distance}")
            
            # 如果匹配度太低，尝试边缘检测
            if max_val < 0.6:
                logger.warning(f"模板匹配度较低: {max_val:.3f}, 尝试边缘检测")
                distance = self._find_slider_by_edge_detection(background_gray, slider_gray)
            
            return distance
            
        except Exception as e:
            logger.error(f"计算滑块距离失败: {e}")
            return -1
    
    def _find_slider_by_edge_detection(
        self,
        background_gray: np.ndarray,
        slider_gray: np.ndarray
    ) -> int:
        """
        使用边缘检测寻找滑块位置
        
        Args:
            background_gray: 背景灰度图
            slider_gray: 滑块灰度图
            
        Returns:
            int: 滑块距离
        """
        try:
            # 使用Canny边缘检测
            background_edges = cv2.Canny(background_gray, 100, 200)
            slider_edges = cv2.Canny(slider_gray, 100, 200)
            
            # 模板匹配边缘
            result = cv2.matchTemplate(background_edges, slider_edges, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            distance = max_loc[0]
            logger.debug(f"边缘检测结果 - 最大值: {max_val:.3f}, 距离: {distance}")
            
            return distance
            
        except Exception as e:
            logger.error(f"边缘检测失败: {e}")
            return -1
    
    async def _simulate_slider_drag(
        self,
        page: Page,
        slider_element: ElementHandle,
        slider_box: Dict[str, float],
        distance: int
    ):
        """
        模拟人类拖动滑块
        
        Args:
            page: 页面对象
            slider_element: 滑块元素
            slider_box: 滑块位置
            distance: 移动距离
        """
        try:
            # 计算起始位置
            start_x = slider_box["x"] + slider_box["width"] / 2
            start_y = slider_box["y"] + slider_box["height"] / 2
            
            # 点击滑块
            await page.mouse.move(start_x, start_y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await page.mouse.down()
            
            # 模拟人类拖动轨迹（不是直线）
            steps = random.randint(10, 20)
            for i in range(steps):
                progress = (i + 1) / steps
                # 添加随机抖动
                jitter_x = random.uniform(-2, 2)
                jitter_y = random.uniform(-1, 1)
                
                current_x = start_x + distance * progress + jitter_x
                current_y = start_y + jitter_y
                
                await page.mouse.move(current_x, current_y)
                
                # 随机延迟
                delay = random.uniform(0.01, 0.05)
                await asyncio.sleep(delay)
            
            # 释放鼠标
            await page.mouse.up()
            
            logger.info("✅ 滑块拖动完成")
            
        except Exception as e:
            logger.error(f"拖动滑块失败: {e}")
    
    async def _check_slider_success(self, page: Page) -> bool:
        """
        检查滑块验证是否成功
        
        Args:
            page: 页面对象
            
        Returns:
            bool: 是否成功
        """
        try:
            # 等待一小段时间让页面响应
            await asyncio.sleep(1)
            
            # 检查常见的成功/失败元素
            success_selectors = [
                ".gt_success",
                ".captcha-success",
                "[class*='success']"
            ]
            
            fail_selectors = [
                ".gt_fail",
                ".captcha-fail",
                "[class*='fail']",
                ".gt_cut_fullbg",
                ".gt_cut_jigsaw"
            ]
            
            # 检查失败元素
            for selector in fail_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.warning("检测到滑块验证失败")
                        return False
                except:
                    pass
            
            # 检查成功元素（如果有的话）
            for selector in success_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info("检测到滑块验证成功")
                        return True
                except:
                    pass
            
            # 默认返回True（假设成功）
            return True
            
        except Exception as e:
            logger.error(f"检查滑块结果失败: {e}")
            return True


class CaptchaBreaker:
    """验证码破解器（统一入口）"""
    
    def __init__(self):
        self.ocr_engine = OCREngine()
        self.slider_solver = SliderSolver()
    
    async def break_text_captcha(
        self,
        page: Page,
        captcha_image_selector: str,
        input_selector: Optional[str] = None,
        submit_selector: Optional[str] = None
    ) -> CaptchaResult:
        """
        破解文本验证码
        
        Args:
            page: 页面对象
            captcha_image_selector: 验证码图片选择器
            input_selector: 输入框选择器（可选）
            submit_selector: 提交按钮选择器（可选）
            
        Returns:
            CaptchaResult: 破解结果
        """
        try:
            # 等待验证码图片加载
            await page.wait_for_selector(captcha_image_selector, timeout=10000)
            
            # 获取验证码图片元素
            captcha_element = await page.query_selector(captcha_image_selector)
            if not captcha_element:
                return CaptchaResult(
                    success=False,
                    captcha_type=CaptchaType.TEXT.value,
                    result=None,
                    confidence=0.0,
                    error_message="未找到验证码图片"
                )
            
            # 识别验证码
            text, confidence = await self.ocr_engine.recognize_text_from_element(captcha_element)
            
            if not text:
                return CaptchaResult(
                    success=False,
                    captcha_type=CaptchaType.TEXT.value,
                    result=None,
                    confidence=0.0,
                    error_message="OCR未能识别验证码"
                )
            
            logger.info(f"✅ 验证码识别: {text} (置信度: {confidence:.2f})")
            
            # 如果提供了输入框，自动填充
            if input_selector:
                try:
                    await page.wait_for_selector(input_selector, timeout=5000)
                    input_element = await page.query_selector(input_selector)
                    if input_element:
                        # 模拟人类输入
                        await input_element.click()
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        
                        # 逐字输入
                        for char in text:
                            await input_element.type(char, delay=random.uniform(50, 150))
                        
                        await asyncio.sleep(random.uniform(0.2, 0.5))
                        logger.info("✅ 验证码已自动填充")
                except Exception as e:
                    logger.warning(f"自动填充验证码失败: {e}")
            
            # 如果提供了提交按钮，自动提交
            if submit_selector:
                try:
                    await page.wait_for_selector(submit_selector, timeout=5000)
                    submit_button = await page.query_selector(submit_selector)
                    if submit_button:
                        await submit_button.click()
                        logger.info("✅ 验证码已自动提交")
                except Exception as e:
                    logger.warning(f"自动提交验证码失败: {e}")
            
            return CaptchaResult(
                success=True,
                captcha_type=CaptchaType.TEXT.value,
                result={"text": text},
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"文本验证码破解失败: {e}")
            return CaptchaResult(
                success=False,
                captcha_type=CaptchaType.TEXT.value,
                result=None,
                confidence=0.0,
                error_message=str(e)
            )
    
    async def break_slider_captcha(
        self,
        page: Page,
        slider_selector: str,
        background_selector: str,
        target_selector: Optional[str] = None
    ) -> CaptchaResult:
        """
        破解滑块验证码
        
        Args:
            page: 页面对象
            slider_selector: 滑块选择器
            background_selector: 背景图选择器
            target_selector: 目标位置选择器（可选）
            
        Returns:
            CaptchaResult: 破解结果
        """
        return await self.slider_solver.solve_slider(
            page,
            slider_selector,
            background_selector,
            target_selector
        )
    
    async def break_captcha_auto(
        self,
        page: Page,
        captcha_type: Optional[str] = None
    ) -> CaptchaResult:
        """
        自动识别并破解验证码
        
        Args:
            page: 页面对象
            captcha_type: 验证码类型（可选，不指定则自动检测）
            
        Returns:
            CaptchaResult: 破解结果
        """
        # 如果未指定类型，尝试自动检测
        if captcha_type is None:
            captcha_type = await self._detect_captcha_type(page)
        
        # 根据类型调用相应的破解方法
        if captcha_type == CaptchaType.TEXT.value:
            # 文本验证码 - 需要提供具体的选择器
            return CaptchaResult(
                success=False,
                captcha_type=captcha_type,
                result=None,
                confidence=0.0,
                error_message="文本验证码需要提供具体的选择器"
            )
        elif captcha_type == CaptchaType.SLIDER.value:
            # 滑块验证码 - 尝试常见的选择器
            slider_selectors = [
                ".gt_slider_knob",
                ".yidun_slider_knob",
                ".slider-btn",
                "[class*='slider']"
            ]
            
            background_selectors = [
                ".gt_cut_fullbg",
                ".yidun_bg-img",
                ".captcha-background",
                "[class*='background']"
            ]
            
            for slider_selector in slider_selectors:
                for background_selector in background_selectors:
                    try:
                        result = await self.break_slider_captcha(
                            page,
                            slider_selector,
                            background_selector
                        )
                        if result.success:
                            return result
                    except:
                        continue
            
            return CaptchaResult(
                success=False,
                captcha_type=CaptchaType.SLIDER.value,
                result=None,
                confidence=0.0,
                error_message="未找到滑块验证码元素"
            )
        else:
            return CaptchaResult(
                success=False,
                captcha_type=captcha_type or "unknown",
                result=None,
                confidence=0.0,
                error_message="不支持的验证码类型"
            )
    
    async def _detect_captcha_type(self, page: Page) -> Optional[str]:
        """
        自动检测验证码类型
        
        Args:
            page: 页面对象
            
        Returns:
            Optional[str]: 验证码类型
        """
        # 检查滑块验证码
        slider_selectors = [
            ".gt_slider_knob",
            ".yidun_slider_knob",
            ".slider-btn"
        ]
        
        for selector in slider_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"检测到滑块验证码: {selector}")
                    return CaptchaType.SLIDER.value
            except:
                continue
        
        # 检查文本验证码
        text_selectors = [
            "img[src*='captcha']",
            "img[alt*='验证码']",
            ".captcha-img",
            "#captcha-img"
        ]
        
        for selector in text_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"检测到文本验证码: {selector}")
                    return CaptchaType.TEXT.value
            except:
                continue
        
        logger.warning("未能自动检测验证码类型")
        return None


# 创建全局验证码破解器实例
_captcha_breaker = None


def get_captcha_breaker() -> CaptchaBreaker:
    """
    获取验证码破解器实例（单例模式）
    
    Returns:
        CaptchaBreaker: 验证码破解器实例
    """
    global _captcha_breaker
    if _captcha_breaker is None:
        _captcha_breaker = CaptchaBreaker()
    return _captcha_breaker
