"""
封面图A/B测试框架
用于测试不同封面图的效果，选择最佳方案
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.utils.logger import logger


class CoverABTest:
    """封面图A/B测试器"""
    
    def __init__(self, test_dir: str = "tests/ab_tests"):
        self.test_dir = test_dir
        os.makedirs(test_dir, exist_ok=True)
        
        # 测试结果存储文件
        self.results_file = os.path.join(test_dir, "test_results.json")
        
        # 加载已有结果
        self.results = self._load_results()
    
    def _load_results(self) -> dict:
        """加载测试结果"""
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_results(self):
        """保存测试结果"""
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
    
    def create_test(
        self,
        test_id: str,
        article_title: str,
        cover_variants: List[Dict[str, Any]],
        description: str = ""
    ) -> Dict[str, Any]:
        """
        创建A/B测试
        
        Args:
            test_id: 测试ID
            article_title: 文章标题
            cover_variants: 封面图变体列表
                [
                    {
                        "variant_id": "A",
                        "file_path": "path/to/cover_a.jpg",
                        "style": "modern",
                        "description": "现代风格"
                    },
                    {
                        "variant_id": "B",
                        "file_path": "path/to/cover_b.jpg",
                        "style": "minimal",
                        "description": "极简风格"
                    }
                ]
            description: 测试描述
            
        Returns:
            测试结果
        """
        try:
            logger.info(f"创建A/B测试: {test_id}")
            
            # 验证变体数量
            if len(cover_variants) < 2:
                return {
                    "status": "failed",
                    "error": "至少需要2个变体进行A/B测试"
                }
            
            # 创建测试记录
            test_record = {
                "test_id": test_id,
                "article_title": article_title,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "variants": cover_variants,
                "metrics": {
                    variant["variant_id"]: {
                        "impressions": 0,
                        "clicks": 0,
                        "ctr": 0.0,
                        "engagement_score": 0.0
                    }
                    for variant in cover_variants
                }
            }
            
            # 保存测试记录
            self.results[test_id] = test_record
            self._save_results()
            
            logger.info(f"✅ A/B测试创建成功: {test_id}")
            
            return {
                "status": "success",
                "test_id": test_id,
                "message": f"已创建 {len(cover_variants)} 个变体的A/B测试",
                "variants": [v["variant_id"] for v in cover_variants]
            }
            
        except Exception as e:
            logger.error(f"❌ 创建A/B测试失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def record_impression(
        self,
        test_id: str,
        variant_id: str,
        user_id: str = None
    ) -> bool:
        """
        记录曝光
        
        Args:
            test_id: 测试ID
            variant_id: 变体ID
            user_id: 用户ID（可选）
            
        Returns:
            是否成功
        """
        if test_id not in self.results:
            logger.warning(f"测试不存在: {test_id}")
            return False
        
        test = self.results[test_id]
        
        if variant_id not in test["metrics"]:
            logger.warning(f"变体不存在: {variant_id}")
            return False
        
        # 增加曝光数
        test["metrics"][variant_id]["impressions"] += 1
        
        # 更新CTR
        self._update_ctr(test_id, variant_id)
        
        self._save_results()
        return True
    
    def record_click(
        self,
        test_id: str,
        variant_id: str,
        user_id: str = None
    ) -> bool:
        """
        记录点击
        
        Args:
            test_id: 测试ID
            variant_id: 变体ID
            user_id: 用户ID（可选）
            
        Returns:
            是否成功
        """
        if test_id not in self.results:
            logger.warning(f"测试不存在: {test_id}")
            return False
        
        test = self.results[test_id]
        
        if variant_id not in test["metrics"]:
            logger.warning(f"变体不存在: {variant_id}")
            return False
        
        # 增加点击数
        test["metrics"][variant_id]["clicks"] += 1
        
        # 更新CTR
        self._update_ctr(test_id, variant_id)
        
        self._save_results()
        return True
    
    def _update_ctr(self, test_id: str, variant_id: str):
        """更新点击率"""
        test = self.results[test_id]
        metrics = test["metrics"][variant_id]
        
        impressions = metrics["impressions"]
        clicks = metrics["clicks"]
        
        if impressions > 0:
            metrics["ctr"] = round(clicks / impressions * 100, 2)
        else:
            metrics["ctr"] = 0.0
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """
        获取测试结果
        
        Args:
            test_id: 测试ID
            
        Returns:
            测试结果
        """
        if test_id not in self.results:
            return {
                "status": "failed",
                "error": f"测试不存在: {test_id}"
            }
        
        test = self.results[test_id]
        
        # 找出最佳变体
        best_variant = None
        best_ctr = 0
        
        for variant_id, metrics in test["metrics"].items():
            if metrics["ctr"] > best_ctr:
                best_ctr = metrics["ctr"]
                best_variant = variant_id
        
        result = {
            "status": "success",
            "test_id": test_id,
            "article_title": test["article_title"],
            "test_status": test["status"],  # 重命名避免冲突
            "created_at": test["created_at"],
            "variants": test["variants"],
            "metrics": test["metrics"],
            "best_variant": best_variant,
            "best_ctr": best_ctr
        }
        
        return result
    
    def get_all_tests(self) -> List[Dict[str, Any]]:
        """获取所有测试"""
        tests = []
        for test_id in self.results:
            test_info = self.get_test_results(test_id)
            if test_info["status"] == "success":
                tests.append(test_info)
        return tests
    
    def end_test(self, test_id: str) -> Dict[str, Any]:
        """
        结束测试并返回最佳变体
        
        Args:
            test_id: 测试ID
            
        Returns:
            测试结果和最佳变体
        """
        if test_id not in self.results:
            return {
                "status": "failed",
                "error": f"测试不存在: {test_id}"
            }
        
        test = self.results[test_id]
        test["status"] = "completed"
        test["ended_at"] = datetime.now().isoformat()
        
        self._save_results()
        
        # 获取最终结果
        result = self.get_test_results(test_id)
        
        logger.info(f"✅ A/B测试结束: {test_id}, 最佳变体: {result['best_variant']}")
        
        return result
    
    def delete_test(self, test_id: str) -> bool:
        """删除测试"""
        if test_id in self.results:
            del self.results[test_id]
            self._save_results()
            logger.info(f"✅ 已删除测试: {test_id}")
            return True
        return False
    
    def generate_test_report(self, test_id: str) -> str:
        """
        生成测试报告
        
        Args:
            test_id: 测试ID
            
        Returns:
            报告文本
        """
        result = self.get_test_results(test_id)
        
        if result["status"] != "success":
            return f"测试不存在: {test_id}"
        
        report = []
        report.append("=" * 80)
        report.append(f"A/B测试报告: {test_id}")
        report.append("=" * 80)
        report.append(f"文章标题: {result['article_title']}")
        report.append(f"测试状态: {result['test_status']}")
        report.append(f"创建时间: {result['created_at']}")
        report.append("")
        report.append("变体对比:")
        report.append("-" * 80)
        
        for variant in result["variants"]:
            variant_id = variant["variant_id"]
            metrics = result["metrics"][variant_id]
            
            report.append(f"\n变体 {variant_id}:")
            report.append(f"  风格: {variant.get('style', 'N/A')}")
            report.append(f"  描述: {variant.get('description', 'N/A')}")
            report.append(f"  曝光数: {metrics['impressions']}")
            report.append(f"  点击数: {metrics['clicks']}")
            report.append(f"  点击率: {metrics['ctr']}%")
        
        report.append("")
        report.append("-" * 80)
        report.append(f"🏆 最佳变体: {result['best_variant']}")
        report.append(f"   点击率: {result['best_ctr']}%")
        report.append("=" * 80)
        
        return "\n".join(report)


# 单例模式
_ab_tester = None

def get_ab_tester() -> CoverABTest:
    """获取A/B测试器单例"""
    global _ab_tester
    if _ab_tester is None:
        _ab_tester = CoverABTest()
    return _ab_tester
