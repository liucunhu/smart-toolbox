from collections import deque
from typing import List, Dict
from app.utils.logger import logger

class ACAutomaton:
    """AC 自动机节点"""
    def __init__(self):
        self.children = {}
        self.fail = None
        self.is_end = False
        self.word = None

class HighPerformanceFilter:
    """基于 AC 自动机的高性能敏感词过滤引擎"""

    def __init__(self):
        self.root = ACAutomaton()
        self.keywords = []
        self.replacements = {
            "微信": "V信", "赚钱": "搞米", "第一": "No.1", 
            "顶级": "天花板", "绝对": "真的"
        }

    def add_keyword(self, word: str):
        """向 Trie 树中添加关键词"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = ACAutomaton()
            node = node.children[char]
        node.is_end = True
        node.word = word

    def build_failure_pointer(self):
        """构建失败指针 (BFS)"""
        queue = deque()
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)

        while queue:
            current_node = queue.popleft()
            for char, child_node in current_node.children.items():
                fail_node = current_node.fail
                while fail_node and char not in fail_node.children:
                    fail_node = fail_node.fail
                
                child_node.fail = fail_node.children[char] if fail_node and char in fail_node.children else self.root
                child_node.is_end = child_node.is_end or child_node.fail.is_end
                queue.append(child_node)

    def load_platform_rules(self, platform: str):
        """加载特定平台的规则并构建自动机"""
        # 模拟从配置加载
        rules = {
            "douyin": ["微信", "私信", "赚钱", "第一", "顶级"],
            "xiaohongshu": ["微信", "购买", "淘宝", "链接"]
        }
        self.keywords = rules.get(platform, [])
        
        # 重置并重新构建
        self.root = ACAutomaton()
        for word in self.keywords:
            self.add_keyword(word)
        self.build_failure_pointer()
        logger.info(f"平台 {platform} 的 AC 自动机已构建，包含 {len(self.keywords)} 个敏感词")

    def filter_text(self, text: str) -> Dict[str, any]:
        """执行过滤"""
        if not self.keywords:
            return {"cleaned_text": text, "violations": [], "is_safe": True}

        violations = set()
        text_list = list(text)
        node = self.root

        for i, char in enumerate(text):
            while node and char not in node.children:
                node = node.fail
            
            if not node:
                node = self.root
                continue
            
            node = node.children.get(char)
            if not node:
                node = self.root
                continue

            # 如果当前节点或其后缀节点是某个词的结尾
            temp_node = node
            while temp_node != self.root:
                if temp_node.is_end and temp_node.word:
                    violations.add(temp_node.word)
                    # 简单替换逻辑：将敏感词部分替换
                    start_idx = i - len(temp_node.word) + 1
                    replacement = self.replacements.get(temp_node.word, "*" * len(temp_node.word))
                    for j, rep_char in enumerate(replacement):
                        if start_idx + j < len(text_list):
                            text_list[start_idx + j] = rep_char
                temp_node = temp_node.fail

        cleaned_text = "".join(text_list)
        return {
            "cleaned_text": cleaned_text,
            "violations": list(violations),
            "is_safe": len(violations) == 0
        }

# 示例调用
if __name__ == "__main__":
    ac_filter = HighPerformanceFilter()
    ac_filter.load_platform_rules("douyin")
    result = ac_filter.filter_text("这个产品绝对是全网第一，想赚钱的加微信！")
    print(result)
