"""
OCR验证码识别服务
支持滑块验证、文字点选、图形验证码
"""
import base64
import httpx
import asyncio
from app.utils.logger import logger
from typing import Dict, Optional


class CaptchaSolver:
    """验证码识别器"""
    
    def __init__(self, api_key: str = "", provider: str = "2captcha"):
        self.api_key = api_key
        self.provider = provider
    
    async def solve_slider_captcha(
        self,
        bg_image_url: str,
        slide_image_url: str
    ) -> Dict:
        """
        解决滑块验证码
        
        Args:
            bg_image_url: 背景图URL
            slide_image_url: 滑块图URL
        
        Returns:
            {
                "status": "success",
                "distance": 250  # 滑动距离
            }
        """
        try:
            import cv2
            import numpy as np
            
            # 下载图片
            async with httpx.AsyncClient() as client:
                bg_resp = await client.get(bg_image_url)
                slide_resp = await client.get(slide_image_url)
            
            # 转换为OpenCV格式
            bg_img = cv2.imdecode(np.frombuffer(bg_resp.content, np.uint8), cv2.IMREAD_COLOR)
            slide_img = cv2.imdecode(np.frombuffer(slide_resp.content, np.uint8), cv2.IMREAD_COLOR)
            
            # 边缘检测
            bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
            bg_edges = cv2.Canny(bg_gray, 50, 150)
            
            # 模板匹配
            slide_gray = cv2.cvtColor(slide_img, cv2.COLOR_BGR2GRAY)
            slide_edges = cv2.Canny(slide_gray, 50, 150)
            
            result = cv2.matchTemplate(bg_edges, slide_edges, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            distance = max_loc[0]
            
            logger.info(f"滑块验证码识别成功，距离: {distance}")
            
            return {
                "status": "success",
                "distance": distance
            }
        
        except ImportError:
            logger.warning("OpenCV未安装，使用第三方API")
            return await self._solve_slider_with_api(bg_image_url, slide_image_url)
        except Exception as e:
            logger.error(f"滑块验证码识别失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _solve_slider_with_api(self, bg_url: str, slide_url: str) -> Dict:
        """使用第三方API解决滑块验证码"""
        try:
            if self.provider == "2captcha":
                # 2Captcha API
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # 提交任务
                    submit_url = "https://2captcha.com/in.php"
                    submit_data = {
                        "key": self.api_key,
                        "method": "hcaptcha",
                        "pageurl": bg_url
                    }
                    
                    submit_resp = await client.post(submit_url, data=submit_data)
                    captcha_id = submit_resp.text.split("|")[1]
                    
                    # 等待结果
                    for _ in range(10):
                        await asyncio.sleep(5)
                        
                        result_url = f"https://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}"
                        result_resp = await client.get(result_url)
                        
                        if "OK|" in result_resp.text:
                            distance = int(result_resp.text.split("|")[1])
                            return {
                                "status": "success",
                                "distance": distance
                            }
                
                return {
                    "status": "failed",
                    "error": "识别超时"
                }
        
        except Exception as e:
            logger.error(f"API识别失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def solve_image_captcha(self, image_url: str) -> Dict:
        """
        解决图形验证码（数字/字母）
        
        Args:
            image_url: 验证码图片URL
        
        Returns:
            {
                "status": "success",
                "text": "ABCD"
            }
        """
        try:
            # 使用第三方OCR服务
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 下载图片
                resp = await client.get(image_url)
                image_base64 = base64.b64encode(resp.content).decode()
                
                # 发送到OCR服务
                if self.provider == "2captcha":
                    return await self._solve_with_2captcha(image_base64)
                else:
                    return await self._solve_with_dama(image_base64)
        
        except Exception as e:
            logger.error(f"图形验证码识别失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _solve_with_2captcha(self, image_base64: str) -> Dict:
        """使用2Captcha服务"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 提交验证码
            submit_url = "https://2captcha.com/in.php"
            submit_data = {
                "key": self.api_key,
                "method": "base64",
                "body": image_base64
            }
            
            submit_resp = await client.post(submit_url, data=submit_data)
            captcha_id = submit_resp.text.split("|")[1]
            
            # 等待结果
            for _ in range(10):
                await asyncio.sleep(5)
                
                result_url = f"https://2captcha.com/res.php?key={self.api_key}&action=get&id={captcha_id}"
                result_resp = await client.get(result_url)
                
                if "OK|" in result_resp.text:
                    text = result_resp.text.split("|")[1]
                    return {
                        "status": "success",
                        "text": text
                    }
            
            return {
                "status": "failed",
                "error": "识别超时"
            }
    
    async def _solve_with_dama(self, image_base64: str) -> Dict:
        """使用打码兔服务（示例）"""
        # TODO: 实现打码兔API对接
        return {
            "status": "failed",
            "error": "未实现"
        }


# 使用示例
if __name__ == "__main__":
    async def test_captcha():
        solver = CaptchaSolver(api_key="YOUR_API_KEY")
        
        # 识别滑块验证码
        result = await solver.solve_slider_captcha(
            bg_image_url="https://example.com/bg.png",
            slide_image_url="https://example.com/slide.png"
        )
        print(result)
        
        # 识别图形验证码
        result = await solver.solve_image_captcha(
            image_url="https://example.com/captcha.png"
        )
        print(result)
    
    asyncio.run(test_captcha())
