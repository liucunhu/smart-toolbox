"""
跨平台知识迁移引擎
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class PlatformKnowledge:
    """平台特定知识"""
    platform: str
    knowledge_type: str  # rules/patterns/best_practices
    content: Dict[str, Any]
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)


class CrossPlatformKnowledgeBase:
    """跨平台知识库"""
    
    def __init__(self):
        self.knowledge_store: Dict[str, List[PlatformKnowledge]] = {}
        self.platform_mappings: Dict[str, Dict[str, str]] = {}
    
    def add_knowledge(
        self,
        platform: str,
        knowledge_type: str,
        content: Dict[str, Any],
        confidence: float = 1.0
    ):
        """添加平台知识"""
        if platform not in self.knowledge_store:
            self.knowledge_store[platform] = []
        
        knowledge = PlatformKnowledge(
            platform=platform,
            knowledge_type=knowledge_type,
            content=content,
            confidence=confidence
        )
        
        self.knowledge_store[platform].append(knowledge)
        logger.info(f"添加{platform}平台知识: {knowledge_type}")
    
    def query_knowledge(
        self,
        platform: str,
        knowledge_type: Optional[str] = None
    ) -> List[PlatformKnowledge]:
        """查询平台知识"""
        if platform not in self.knowledge_store:
            return []
        
        knowledge_list = self.knowledge_store[platform]
        
        if knowledge_type:
            knowledge_list = [k for k in knowledge_list if k.knowledge_type == knowledge_type]
        
        # 按置信度排序
        return sorted(knowledge_list, key=lambda k: k.confidence, reverse=True)
    
    def transfer_knowledge(
        self,
        source_platform: str,
        target_platform: str,
        knowledge_type: str
    ) -> Optional[Dict[str, Any]]:
        """从一个平台迁移知识到另一个平台"""
        # 获取源平台知识
        source_knowledge = self.query_knowledge(source_platform, knowledge_type)
        
        if not source_knowledge:
            return None
        
        # 使用最佳实践（置信度最高）
        best_knowledge = source_knowledge[0]
        
        # 应用平台映射转换
        transferred_content = self._apply_platform_mapping(
            best_knowledge.content,
            source_platform,
            target_platform
        )
        
        logger.info(f"知识迁移: {source_platform} -> {target_platform} ({knowledge_type})")
        
        return {
            "source_platform": source_platform,
            "target_platform": target_platform,
            "transferred_content": transferred_content,
            "original_confidence": best_knowledge.confidence
        }
    
    def _apply_platform_mapping(
        self,
        content: Dict[str, Any],
        source_platform: str,
        target_platform: str
    ) -> Dict[str, Any]:
        """应用平台映射转换内容"""
        mapping_key = f"{source_platform}_to_{target_platform}"
        
        if mapping_key in self.platform_mappings:
            mapping = self.platform_mappings[mapping_key]
            # 根据映射规则转换内容
            transformed = {}
            for key, value in content.items():
                mapped_key = mapping.get(key, key)
                transformed[mapped_key] = value
            return transformed
        
        # 如果没有映射，直接返回
        return content
    
    def register_platform_mapping(
        self,
        source_platform: str,
        target_platform: str,
        mapping: Dict[str, str]
    ):
        """注册平台映射规则"""
        mapping_key = f"{source_platform}_to_{target_platform}"
        self.platform_mappings[mapping_key] = mapping
        logger.info(f"注册平台映射: {mapping_key}")


class PlatformAdapter:
    """平台适配器 - 统一不同平台接口"""
    
    def __init__(self):
        self.adapters: Dict[str, Dict[str, Any]] = {}
    
    def register_adapter(self, platform: str, adapter_config: Dict[str, Any]):
        """注册平台适配器"""
        self.adapters[platform] = adapter_config
        logger.info(f"注册平台适配器: {platform}")
    
    def normalize_request(
        self,
        platform: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """标准化请求为平台特定格式"""
        if platform not in self.adapters:
            raise ValueError(f"未找到平台适配器: {platform}")
        
        adapter = self.adapters[platform]
        
        # 应用字段映射
        normalized = {}
        field_mapping = adapter.get("field_mapping", {})
        
        for key, value in request.items():
            mapped_key = field_mapping.get(key, key)
            normalized[mapped_key] = value
        
        # 添加平台特定参数
        platform_specific = adapter.get("platform_specific", {})
        normalized.update(platform_specific)
        
        return normalized
    
    def denormalize_response(
        self,
        platform: str,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将平台响应转换为标准格式"""
        if platform not in self.adapters:
            raise ValueError(f"未找到平台适配器: {platform}")
        
        adapter = self.adapters[platform]
        
        # 反向字段映射
        field_mapping = adapter.get("field_mapping", {})
        reverse_mapping = {v: k for k, v in field_mapping.items()}
        
        denormalized = {}
        for key, value in response.items():
            original_key = reverse_mapping.get(key, key)
            denormalized[original_key] = value
        
        return denormalized


class TransferLearningEngine:
    """迁移学习引擎"""
    
    def __init__(self):
        self.knowledge_base = CrossPlatformKnowledgeBase()
        self.transfer_history: List[Dict[str, Any]] = []
    
    def learn_from_platform(
        self,
        platform: str,
        experience_data: List[Dict[str, Any]]
    ):
        """从平台经验中学习"""
        logger.info(f"从{platform}平台学习 {len(experience_data)}条经验")
        
        for exp in experience_data:
            # 提取模式和规则
            patterns = self._extract_patterns(exp)
            best_practices = self._extract_best_practices(exp)
            
            # 存储到知识库
            if patterns:
                self.knowledge_base.add_knowledge(
                    platform=platform,
                    knowledge_type="patterns",
                    content=patterns,
                    confidence=exp.get("confidence", 0.8)
                )
            
            if best_practices:
                self.knowledge_base.add_knowledge(
                    platform=platform,
                    knowledge_type="best_practices",
                    content=best_practices,
                    confidence=exp.get("confidence", 0.9)
                )
    
    def apply_to_platform(
        self,
        source_platform: str,
        target_platform: str,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将源平台知识应用到目标平台"""
        # 迁移知识
        transferred = self.knowledge_base.transfer_knowledge(
            source_platform=source_platform,
            target_platform=target_platform,
            knowledge_type="best_practices"
        )
        
        if not transferred:
            return {
                "success": False,
                "message": "无可迁移的知识"
            }
        
        # 记录迁移历史
        self.transfer_history.append({
            "id": str(uuid.uuid4()),
            "source": source_platform,
            "target": target_platform,
            "timestamp": datetime.now().isoformat(),
            "context": task_context
        })
        
        return {
            "success": True,
            "transferred_knowledge": transferred,
            "adaptation_suggestions": self._generate_adaptation_suggestions(
                source_platform,
                target_platform,
                transferred["transferred_content"]
            )
        }
    
    def _extract_patterns(self, experience: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从经验中提取模式"""
        # 简单实现：提取成功的关键因素
        if experience.get("result") == "success":
            return {
                "successful_factors": experience.get("factors", []),
                "context_conditions": experience.get("conditions", {})
            }
        return None
    
    def _extract_best_practices(self, experience: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从经验中提取最佳实践"""
        if experience.get("result") == "success" and experience.get("reward", 0) > 0.7:
            return {
                "action": experience.get("action"),
                "parameters": experience.get("parameters", {}),
                "performance_metrics": experience.get("metrics", {})
            }
        return None
    
    def _generate_adaptation_suggestions(
        self,
        source: str,
        target: str,
        transferred_content: Dict[str, Any]
    ) -> List[str]:
        """生成适配建议"""
        suggestions = [
            f"根据{target}平台特性调整参数",
            "验证迁移知识的适用性",
            "进行小规模测试后再全面应用"
        ]
        
        return suggestions
    
    def get_transfer_statistics(self) -> Dict[str, Any]:
        """获取迁移统计"""
        total_transfers = len(self.transfer_history)
        
        # 按平台对统计
        platform_pairs = {}
        for transfer in self.transfer_history:
            pair_key = f"{transfer['source']}->{transfer['target']}"
            platform_pairs[pair_key] = platform_pairs.get(pair_key, 0) + 1
        
        return {
            "total_transfers": total_transfers,
            "platform_pairs": platform_pairs,
            "knowledge_base_size": sum(
                len(v) for v in self.knowledge_base.knowledge_store.values()
            )
        }
