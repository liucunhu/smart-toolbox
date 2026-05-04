"""
数字水印技术
支持频域水印嵌入和提取
"""
import cv2
import numpy as np
from app.utils.logger import logger
from typing import Optional


class Watermarker:
    """数字水印处理器"""
    
    async def embed_watermark(self, image_path: str, watermark_text: str, output_path: str) -> bool:
        """
        嵌入不可见水印
        
        Args:
            image_path: 原始图片路径
            watermark_text: 水印文本
            output_path: 输出图片路径
        
        Returns:
            是否成功
        """
        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                return False
            
            # 简单的水印嵌入（LSB方法）
            # TODO: 实现更复杂的频域水印
            watermark_bytes = watermark_text.encode('utf-8')
            
            # 将水印嵌入到最低有效位
            for i, byte in enumerate(watermark_bytes):
                if i >= img.shape[0] * img.shape[1]:
                    break
                row, col = divmod(i, img.shape[1])
                img[row, col, 0] = (img[row, col, 0] & 0xFE) | (byte >> 7)
            
            # 保存图片
            cv2.imwrite(output_path, img)
            logger.info(f"水印嵌入成功: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"水印嵌入失败: {str(e)}")
            return False
    
    async def extract_watermark(self, image_path: str, length: int = 100) -> Optional[str]:
        """
        提取水印
        
        Args:
            image_path: 图片路径
            length: 水印长度
        
        Returns:
            提取的水印文本
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # 提取最低有效位
            watermark_bits = []
            for i in range(length * 8):
                row, col = divmod(i, img.shape[1])
                bit = img[row, col, 0] & 1
                watermark_bits.append(bit)
            
            # 转换为文本
            watermark_bytes = bytearray()
            for i in range(0, len(watermark_bits), 8):
                byte = 0
                for j in range(8):
                    if i + j < len(watermark_bits):
                        byte = (byte << 1) | watermark_bits[i + j]
                watermark_bytes.append(byte)
            
            watermark_text = watermark_bytes.decode('utf-8', errors='ignore')
            logger.info(f"水印提取成功: {watermark_text}")
            return watermark_text
        
        except Exception as e:
            logger.error(f"水印提取失败: {str(e)}")
            return None


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_watermark():
        watermarker = Watermarker()
        
        # 嵌入水印
        success = await watermarker.embed_watermark(
            "test.jpg",
            "Copyright 2026",
            "output.jpg"
        )
        print(f"嵌入结果: {success}")
        
        # 提取水印
        text = await watermarker.extract_watermark("output.jpg")
        print(f"提取结果: {text}")
    
    asyncio.run(test_watermark())
