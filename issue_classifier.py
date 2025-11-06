import re
from typing import Dict, List, Tuple, Optional

class IssueClassifier:
    def __init__(self):
        # Bug关键词库 - 按权重排序
        self.bug_keywords = {
            # 高权重 - 明确指向bug
            'high': [
                'crash', 'broken', 'error', 'exception', 'failed', 'failure', 'bug', 'issue',
                'incorrect', 'wrong', 'unexpected', 'regression', 'defect', 'glitch', 'flaw',
                '崩溃', '错误', '失败', '异常', '故障', '缺陷', '问题', '不正确', '意外'
            ],
            # 中权重 - 可能是bug
            'medium': [
                'fix', 'patch', 'repair', 'debug', 'troubleshoot', 'not working', 'does not work',
                'unable to', 'cannot', 'can\'t', 'won\'t', 'doesn\'t', 'problem', 'conflict',
                '修复', '调试', '无法', '不能', '冲突', '解决', '处理'
            ],
            # 低权重 - 间接相关
            'low': [
                'improve', 'optimize', 'refactor', 'cleanup', 'update', 'upgrade', 'migrate',
                '改进', '优化', '重构', '清理', '更新', '升级', '迁移'
            ]
        }

        # Enhancement关键词库
        self.enhancement_keywords = {
            # 高权重 - 明确指向新功能
            'high': [
                'feature', 'enhancement', 'add', 'new', 'implement', 'introduce', 'support',
                'request', 'propose', 'suggest', 'wish', 'extend', 'expand', 'create',
                '功能', '增强', '添加', '新增', '实现', '引入', '支持', '请求', '建议', '希望', '扩展', '创建'
            ],
            # 中权重 - 功能相关
            'medium': [
                'allow', 'enable', 'provide', 'option', 'setting', 'config', 'custom',
                'ability', 'capability', 'integration', 'api', 'interface', 'module',
                '允许', '启用', '提供', '选项', '设置', '配置', '自定义', '能力', '集成', '接口', '模块'
            ],
            # 低权重 - 改进性功能
            'low': [
                'improve', 'enhance', 'upgrade', 'extend', 'expand', 'modify', 'change',
                '改进', '增强', '升级', '扩展', '修改', '变更'
            ]
        }

        # 模板匹配模式
        self.template_patterns = {
            'bug': [
                r'bug\s+report\s+template',
                r'bug\s+template',
                r'issue\s+template',
                r'error\s+report',
                r'故障报告模板',
                r'问题报告模板'
            ],
            'enhancement': [
                r'feature\s+request\s+template',
                r'feature\s+template',
                r'enhancement\s+request',
                r'功能请求模板',
                r'功能建议模板'
            ]
        }

        # 排除词 - 这些词出现时倾向于分类为other
        self.exclude_keywords = {
            'other': [
                'question', 'help', 'discussion', 'info', 'information', 'clarification',
                'documentation', 'readme', 'guide', 'tutorial', 'example', 'meta',
                '问题', '帮助', '讨论', '信息', '说明', '文档', '指南', '教程', '示例', '元'
            ]
        }

    def _calculate_score(self, text: str, keyword_dict: Dict[str, List[str]]) -> float:
        """
        计算文本与关键词库的匹配分数
        """
        if not text:
            return 0.0

        text_lower = text.lower()
        total_score = 0.0

        for weight_level, keywords in keyword_dict.items():
            weight_multiplier = {'high': 3.0, 'medium': 2.0, 'low': 1.0}[weight_level]

            for keyword in keywords:
                # 完整单词匹配，避免部分匹配导致的误判
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                total_score += matches * weight_multiplier

        return total_score

    def _check_templates(self, text: str) -> Tuple[float, str]:
        if not text:
            return 0.0, 'other'

        text_lower = text.lower()

        for category, patterns in self.template_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return 10.0, category  # 模板匹配给予高权重

        return 0.0, 'other'

    def _check_exclude_patterns(self, text: str) -> float:
        if not text:
            return 0.0

        text_lower = text.lower()
        exclude_count = 0

        for keyword in self.exclude_keywords['other']:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            exclude_count += len(re.findall(pattern, text_lower, re.IGNORECASE))

        return exclude_count * 2.0  # 排除词给予负向权重

    def classify_issue(self, title: str = "", body: str = "", labels: List[str] = None) -> str:
        # 合并所有文本内容
        combined_text = f"{title} {body}"

        # 处理标签
        label_text = ""
        if labels:
            label_text = " ".join(str(label) for label in labels)
            combined_text += f" {label_text}"

        # 1. 检查模板匹配
        template_score, template_category = self._check_templates(combined_text)
        if template_score > 0:
            return template_category

        # 2. 计算bug和enhancement的分数
        bug_score = self._calculate_score(combined_text, self.bug_keywords)
        enhancement_score = self._calculate_score(combined_text, self.enhancement_keywords)

        # 3. 检查排除词
        exclude_score = self._check_exclude_patterns(combined_text)

        # 4. 标签加分
        if labels:
            for label in labels:
                label_lower = str(label).lower()
                if 'bug' in label_lower or 'fix' in label_lower:
                    bug_score += 2.0
                elif 'feature' in label_lower or 'enhancement' in label_lower or 'request' in label_lower:
                    enhancement_score += 2.0

        # 5. 综合判断
        final_bug_score = bug_score - exclude_score * 0.5
        final_enhancement_score = enhancement_score - exclude_score * 0.5

        # 6. 决策逻辑
        min_threshold = 1.0  # 最小阈值

        if exclude_score > 5.0:  # 排除词过多，直接分类为other
            return 'other'
        elif final_bug_score > final_enhancement_score and final_bug_score >= min_threshold:
            return 'bug'
        elif final_enhancement_score > final_bug_score and final_enhancement_score >= min_threshold:
            return 'enhancement'
        else:
            return 'other'

    def get_classification_confidence(self, title: str = "", body: str = "", labels: List[str] = None) -> Tuple[str, float]:
        combined_text = f"{title} {body}"
        if labels:
            combined_text += " " + " ".join(str(label) for label in labels)

        category = self.classify_issue(title, body, labels)

        # 计算置信度
        bug_score = self._calculate_score(combined_text, self.bug_keywords)
        enhancement_score = self._calculate_score(combined_text, self.enhancement_keywords)
        exclude_score = self._check_exclude_patterns(combined_text)

        if category == 'bug':
            confidence = min(bug_score / (bug_score + enhancement_score + 1.0), 1.0)
        elif category == 'enhancement':
            confidence = min(enhancement_score / (bug_score + enhancement_score + 1.0), 1.0)
        else:
            confidence = exclude_score / (exclude_score + bug_score + enhancement_score + 1.0)

        return category, confidence


# 全局分类器实例
classifier = IssueClassifier()

# 便捷函数
def classify_issue(title: str = "", body: str = "", labels: List[str] = None) -> str:
    """便捷的分类函数"""
    return classifier.classify_issue(title, body, labels)

def classify_issue_with_confidence(title: str = "", body: str = "", labels: List[str] = None) -> Tuple[str, float]:
    """便捷的分类函数（带置信度）"""
    return classifier.get_classification_confidence(title, body, labels)