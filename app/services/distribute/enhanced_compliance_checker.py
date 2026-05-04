"""
增强版合规检查服务
实现违禁词标红显示和谐音/拼音替换建议
"""
import re
import logging
import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.distribute.ac_filter import HighPerformanceFilter

logger = logging.getLogger(__name__)


class HighlightType(Enum):
    """高亮类型"""
    BANNED = "banned"  # 违禁词
    SUSPICIOUS = "suspicious"  # 可疑词
    SUGGESTION = "suggestion"  # 替换建议


@dataclass
class ComplianceCheckResult:
    """合规检查结果"""
    passed: bool
    text: str
    highlighted_text: str  # 带HTML标签的文本
    violations: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    statistics: Dict[str, int]
    platform: str


class PhoneticReplacer:
    """谐音替换器"""
    
    # 常见违禁词的谐音替换映射
    PHONETIC_MAP = {
        # 极限词
        "第一": ["榜首", "领先", "优秀"],
        "最": ["很", "非常", "格外", "特别"],
        "顶级": ["高级", "优质", "精品"],
        "极品": ["优选", "佳品", "精品"],
        "冠军": ["领先", "优胜", "优秀"],
        "绝对": ["相对", "基本", "总体"],
        "唯一": ["独特", "稀有", "少见"],
        "独家": ["特别", "专属", "独家"],
        "首个": ["首批", "早期", "前期"],
        "首个": ["首批", "早期", "前期"],
        
        # 虚假宣传
        "永久": ["长期", "持续", "一直"],
        "终身": ["长期", "持续", "一直"],
        "100%": ["95%", "99%", "高"],
        "零风险": ["低风险", "可控风险"],
        "无风险": ["低风险", "可控风险"],
        "无副作用": ["副作用小", "安全性高"],
        "包治百病": ["效果显著", "疗效明显"],
        "万能": ["多功能", "综合"],
        
        # 财经/医疗
        "保本": ["稳健", "安全"],
        "无亏损": ["低风险", "稳健"],
        "稳赚": ["收益稳定", "回报可观"],
        "收益翻倍": ["收益可观", "回报丰厚"],
        "零门槛": ["门槛低", "易入手"],
        "秒到账": ["快速到账", "即时到账"],
        "根治": ["改善", "缓解", "调理"],
        "治疗": ["调理", "缓解", "改善"],
        "治愈": ["康复", "好转", "缓解"],
        
        # 引流词
        "加微信": ["私信我", "联系我"],
        "加V": ["私信", "留言"],
        "扫码": ["点击链接", "点击查看"],
        "点击": ["访问", "进入", "查看"],
        "链接": ["地址", "路径"],
    }
    
    def get_replacement_suggestions(self, word: str, context: str = "") -> List[str]:
        """
        获取替换建议
        
        Args:
            word: 需要替换的词
            context: 上下文（用于更精准的建议）
            
        Returns:
            List[str]: 替换建议列表
        """
        suggestions = []
        
        # 查找精确匹配
        if word in self.PHONETIC_MAP:
            suggestions = self.PHONETIC_MAP[word].copy()
        
        # 查找包含匹配（部分匹配）
        for key, values in self.PHONETIC_MAP.items():
            if key in word or word in key:
                for value in values:
                    if value not in suggestions:
                        suggestions.append(value)
        
        # 如果没有找到，使用通用替换
        if not suggestions:
            suggestions = self._generate_generic_replacements(word)
        
        return suggestions[:5]  # 最多返回5个建议
    
    def _generate_generic_replacements(self, word: str) -> List[str]:
        """
        生成通用替换建议
        
        Args:
            word: 原词
            
        Returns:
            List[str]: 替换建议列表
        """
        suggestions = []
        
        # 使用同义词替换
        if "最" in word:
            suggestions.extend(["很", "非常", "格外"])
        elif "第一" in word:
            suggestions.extend(["领先", "优秀", "前列"])
        elif "保" in word or "赚" in word:
            suggestions.extend(["收益可观", "回报稳定", "效果良好"])
        else:
            # 模糊化处理
            suggestions.append(f"相关")
            suggestions.append(f"优秀")
        
        return suggestions


class PinyinConverter:
    """拼音转换器"""
    
    # 常见违禁词的拼音
    PINYIN_MAP = {
        # 极限词
        "zuì": "zui",  # 最 → 醉
        "dìyī": "diyi",  # 第一
        "dǐngjí": "dingji",  # 顶级
        "jíduān": "jiduan",  # 极端
        
        # 虚假宣传
        "yǒngjiǔ": "yongjiu",  # 永久
        "zhōngshēn": "zhongshen",  # 终身
        "bǎozhì": "baozhi",  # 保证
        "bǎozhèng": "baozheng",  # 保证
        
        # 医疗
        "zhìliáo": "zhiliao",  # 治疗
        "gēnzhi": "genzhi",  # 根治
        "yùfáng": "yufang",  # 预防
    }
    
    def convert_to_pinyin(self, word: str) -> List[str]:
        """
        将词语转换为拼音
        
        Args:
            word: 词语
            
        Returns:
            List[str]: 拼音变体列表
        """
        variations = []
        
        # 如果在映射表中，使用映射
        for pinyin, replacement in self.PINYIN_MAP.items():
            if pinyin in word.lower():
                variations.append(word.lower().replace(pinyin, replacement))
        
        # 如果没有映射，生成通用拼音
        if not variations:
            variations = self._generate_generic_pinyin(word)
        
        return variations[:3]
    
    def _generate_generic_pinyin(self, word: str) -> List[str]:
        """
        生成通用拼音变体
        
        Args:
            word: 词语
            
        Returns:
            List[str]: 拼音变体列表
        """
        # 简单模拟：将中文替换为占位符
        return [
            word.replace("最", "zui"),
            word.replace("治", "zhi"),
            word.replace("药", "yao"),
        ]


class EnhancedComplianceChecker:
    """增强版合规检查器"""
    
    def __init__(self):
        self.base_checker = HighPerformanceFilter()
        self.phonetic_replacer = PhoneticReplacer()
        self.pinyin_converter = PinyinConverter()
    
    def check_with_highlights(
        self,
        text: str,
        platform: str = "default"
    ) -> ComplianceCheckResult:
        """
        检查文本并返回带高亮的HTML
        
        Args:
            text: 待检查文本
            platform: 平台名称
            
        Returns:
            ComplianceCheckResult: 检查结果
        """
        try:
            # 基础合规检查
            base_result = self.base_checker.check_and_replace(text, platform)
            
            # 分析文本
            violations = self._analyze_violations(text, platform)
            suggestions = self._generate_suggestions(text, violations)
            
            # 生成高亮文本
            highlighted_text = self._highlight_text(text, violations, suggestions)
            
            # 统计信息
            statistics = self._calculate_statistics(text, violations, suggestions)
            
            passed = base_result.get("is_safe", False)
            
            result = ComplianceCheckResult(
                passed=passed,
                text=text,
                highlighted_text=highlighted_text,
                violations=violations,
                suggestions=suggestions,
                statistics=statistics,
                platform=platform
            )
            
            logger.info(f"合规检查完成: 通过={passed}, 违规={len(violations)}, 建议={len(suggestions)}")
            return result
            
        except Exception as e:
            logger.error(f"合规检查失败: {e}")
            return ComplianceCheckResult(
                passed=False,
                text=text,
                highlighted_text=text,
                violations=[],
                suggestions=[],
                statistics={"total_words": len(text)},
                platform=platform
            )
    
    def _analyze_violations(
        self,
        text: str,
        platform: str
    ) -> List[Dict[str, Any]]:
        """
        分析违规词
        
        Args:
            text: 文本
            platform: 平台
            
        Returns:
            List[Dict]: 违规词列表
        """
        violations = []
        
        # 加载平台规则
        self.base_checker.load_platform_rules(platform)
        
        # 检查每个敏感词
        for word in self.base_checker.keywords:
            if word in text:
                # 找到所有出现位置
                positions = []
                start = 0
                while True:
                    pos = text.find(word, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                
                # 记录每个位置
                for pos in positions:
                    violations.append({
                        "word": word,
                        "position": pos,
                        "end": pos + len(word),
                        "type": "banned",
                        "severity": self._get_severity(word, platform),
                        "category": self._get_category(word, platform)
                    })
        
        # 按位置排序
        violations.sort(key=lambda x: x["position"])
        
        return violations
    
    def _get_severity(self, word: str, platform: str) -> str:
        """
        获取违规词严重程度
        
        Args:
            word: 违规词
            platform: 平台
            
        Returns:
            str: 严重程度
        """
        # 极限词 - 高严重
        extreme_words = ["最", "第一", "唯一", "顶级", "极致", "永久"]
        if any(extreme in word for extreme in extreme_words):
            return "high"
        
        # 虚假宣传 - 中严重
        fake_words = ["保证", "包治", "100%", "零风险"]
        if any(fake in word for fake in fake_words):
            return "medium"
        
        # 其他 - 低严重
        return "low"
    
    def _get_category(self, word: str, platform: str) -> str:
        """
        获取违规词分类
        
        Args:
            word: 违规词
            platform: 平台
            
        Returns:
            str: 分类
        """
        categories = {
            "limit_words": ["最", "第一", "唯一", "顶级"],
            "fake_words": ["保证", "包治", "100%", "零风险", "永久"],
            "medical_words": ["治疗", "治愈", "根治", "药", "疗效"],
            "financial_words": ["保本", "稳赚", "收益翻倍", "无亏损"],
            "lead_words": ["加微信", "扫码", "链接", "点击"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in word for keyword in keywords):
                return category
        
        return "other"
    
    def _generate_suggestions(
        self,
        text: str,
        violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        生成替换建议
        
        Args:
            text: 原文
            violations: 违规词列表
            
        Returns:
            List[Dict]: 建议列表
        """
        suggestions = []
        
        for violation in violations:
            word = violation["word"]
            position = violation["position"]
            
            # 获取谐音替换建议
            phonetic_suggestions = self.phonetic_replacer.get_replacement_suggestions(word, text)
            
            # 获取拼音替换建议
            pinyin_suggestions = self.pinyin_converter.convert_to_pinyin(word)
            
            # 组合建议
            all_suggestions = phonetic_suggestions + pinyin_suggestions
            all_suggestions = list(set(all_suggestions))  # 去重
            
            suggestion_entry = {
                "original": word,
                "position": position,
                "phonetic_replacements": phonetic_suggestions[:3],
                "pinyin_replacements": pinyin_suggestions[:3],
                "all_suggestions": all_suggestions[:5],
                "context": self._get_context(text, position, 10)
            }
            
            suggestions.append(suggestion_entry)
        
        return suggestions
    
    def _get_context(self, text: str, position: int, context_length: int = 10) -> str:
        """
        获取上下文
        
        Args:
            text: 文本
            position: 位置
            context_length: 上下文长度
            
        Returns:
            str: 上下文
        """
        start = max(0, position - context_length)
        end = min(len(text), position + context_length + 10)
        return text[start:end]
    
    def _highlight_text(
        self,
        text: str,
        violations: List[Dict[str, Any]],
        suggestions: List[Dict[str, Any]]
    ) -> str:
        """
        生成带高亮的HTML文本
        
        Args:
            text: 原文
            violations: 违规词列表
            suggestions: 建议列表
            
        Returns:
            str: HTML文本
        """
        if not violations:
            return text
        
        # 创建HTML字符串
        html_parts = []
        last_end = 0
        
        # 创建位置到建议的映射
        suggestion_map = {s["position"]: s for s in suggestions}
        
        for violation in violations:
            position = violation["position"]
            end = violation["end"]
            word = violation["word"]
            severity = violation["severity"]
            
            # 添加违规词之前的文本
            html_parts.append(text[last_end:position])
            
            # 添加高亮的违规词
            severity_color = {
                "high": "red",
                "medium": "orange",
                "low": "yellow"
            }.get(severity, "yellow")
            
            # 查找建议
            suggestion = suggestion_map.get(position)
            suggestion_text = ""
            if suggestion and suggestion["all_suggestions"]:
                replacement = suggestion["all_suggestions"][0]
                suggestion_text = f'建议替换为：<strong>{replacement}</strong>'
            
            html_parts.append(
                f'<mark class="violation-{severity}" style="background-color: {severity_color}; padding: 2px 4px; border-radius: 3px;">'
                f'{word}'
                f'<sup style="font-size: 10px; margin-left: 2px;" title="{suggestion_text}">ℹ️</sup>'
                f'</mark>'
            )
            
            last_end = end
        
        # 添加剩余文本
        html_parts.append(text[last_end:])
        
        return "".join(html_parts)
    
    def _calculate_statistics(
        self,
        text: str,
        violations: List[Dict[str, Any]],
        suggestions: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        计算统计信息
        
        Args:
            text: 文本
            violations: 违规词列表
            suggestions: 建议列表
            
        Returns:
            Dict: 统计信息
        """
        total_chars = len(text)
        violation_chars = sum(v["end"] - v["position"] for v in violations)
        
        # 按严重程度统计
        severity_stats = {"high": 0, "medium": 0, "low": 0}
        for v in violations:
            severity_stats[v["severity"]] += 1
        
        # 按分类统计
        category_stats = {}
        for v in violations:
            category = v["category"]
            category_stats[category] = category_stats.get(category, 0) + 1
        
        return {
            "total_chars": total_chars,
            "total_violations": len(violations),
            "violation_chars": violation_chars,
            "violation_rate": round(violation_chars / total_chars * 100, 2) if total_chars > 0 else 0,
            "total_suggestions": len(suggestions),
            "severity_stats": severity_stats,
            "category_stats": category_stats
        }
    
    def get_compliance_report(self, result: ComplianceCheckResult) -> str:
        """
        生成合规检查报告
        
        Args:
            result: 检查结果
            
        Returns:
            str: HTML报告
        """
        report = f"""
        <div class="compliance-report">
            <h2>合规检查报告</h2>
            
            <div class="summary">
                <h3>摘要</h3>
                <p><strong>状态:</strong> {'✅ 通过' if result.passed else '❌ 未通过'}</p>
                <p><strong>平台:</strong> {result.platform}</p>
                <p><strong>文本长度:</strong> {result.statistics['total_chars']} 字符</p>
                <p><strong>违规数量:</strong> {result.statistics['total_violations']}</p>
                <p><strong>违规率:</strong> {result.statistics['violation_rate']}%</p>
            </div>
            
            <div class="violations">
                <h3>违规详情</h3>
                {self._format_violations(result.violations)}
            </div>
            
            <div class="suggestions">
                <h3>替换建议</h3>
                {self._format_suggestions(result.suggestions)}
            </div>
            
            <div class="highlighted-text">
                <h3>高亮文本</h3>
                <div class="text-content">{result.highlighted_text}</div>
            </div>
        </div>
        """
        return report
    
    def _format_violations(self, violations: List[Dict[str, Any]]) -> str:
        """格式化违规列表"""
        if not violations:
            return "<p>未发现违规</p>"
        
        html = "<ul>"
        for v in violations:
            html += f"""
                <li>
                    <strong>{v['word']}</strong>
                    <span class="severity-{v['severity']}">({v['severity']})</span>
                    <span class="category">{v['category']}</span>
                    <span class="position">位置: {v['position']}</span>
                </li>
            """
        html += "</ul>"
        return html
    
    def _format_suggestions(self, suggestions: List[Dict[str, Any]]) -> str:
        """格式化建议列表"""
        if not suggestions:
            return "<p>无建议</p>"
        
        html = "<ul>"
        for s in suggestions:
            replacements = "、".join(s["all_suggestions"])
            html += f"""
                <li>
                    <strong>{s['original']}</strong>
                    <span>→ 建议: {replacements}</span>
                    <span class="context">"{s['context']}"</span>
                </li>
            """
        html += "</ul>"
        return html


# 创建全局增强合规检查器实例
_enhanced_checker = None


def get_enhanced_compliance_checker() -> EnhancedComplianceChecker:
    """
    获取增强版合规检查器实例（单例模式）
    
    Returns:
        EnhancedComplianceChecker: 检查器实例
    """
    global _enhanced_checker
    if _enhanced_checker is None:
        _enhanced_checker = EnhancedComplianceChecker()
    return _enhanced_checker
