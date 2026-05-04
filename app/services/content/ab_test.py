"""
A/B测试引擎
支持多版本文案和封面的A/B测试
"""
from app.utils.logger import logger
from typing import Dict, List
import random


class ABTestEngine:
    """A/B测试引擎"""
    
    def __init__(self):
        self.tests = {}
    
    def create_test(self, test_name: str, variants: List[Dict]) -> str:
        """
        创建A/B测试
        
        Args:
            test_name: 测试名称
            variants: 变体列表，每个变体包含标题、内容等
        
        Returns:
            测试ID
        """
        test_id = f"ab_{test_name}_{random.randint(1000, 9999)}"
        
        self.tests[test_id] = {
            "name": test_name,
            "variants": variants,
            "results": {v["id"]: {"views": 0, "likes": 0, "shares": 0} for v in variants},
            "status": "active"
        }
        
        logger.info(f"A/B测试创建成功: {test_id}")
        return test_id
    
    def get_variant(self, test_id: str) -> Dict:
        """获取随机变体"""
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        variants = test["variants"]
        
        # 随机选择一个变体
        selected = random.choice(variants)
        
        # 记录展示
        self.tests[test_id]["results"][selected["id"]]["views"] += 1
        
        return selected
    
    def record_interaction(self, test_id: str, variant_id: str, interaction_type: str):
        """记录用户交互"""
        if test_id not in self.tests:
            return
        
        if interaction_type in self.tests[test_id]["results"][variant_id]:
            self.tests[test_id]["results"][variant_id][interaction_type] += 1
    
    def get_results(self, test_id: str) -> Dict:
        """获取测试结果"""
        if test_id not in self.tests:
            return {"error": "测试不存在"}
        
        test = self.tests[test_id]
        results = test["results"]
        
        # 计算胜率
        best_variant = max(results.items(), key=lambda x: x[1]["likes"])
        
        return {
            "test_id": test_id,
            "test_name": test["name"],
            "status": test["status"],
            "results": results,
            "best_variant": best_variant[0],
            "best_performance": best_variant[1]
        }
    
    def stop_test(self, test_id: str):
        """停止测试"""
        if test_id in self.tests:
            self.tests[test_id]["status"] = "stopped"
            logger.info(f"A/B测试已停止: {test_id}")


# 使用示例
if __name__ == "__main__":
    engine = ABTestEngine()
    
    # 创建测试
    test_id = engine.create_test("title_test", [
        {"id": "v1", "title": "标题版本1"},
        {"id": "v2", "title": "标题版本2"}
    ])
    
    # 获取变体
    variant = engine.get_variant(test_id)
    print(f"选中变体: {variant}")
    
    # 获取结果
    results = engine.get_results(test_id)
    print(f"测试结果: {results}")
