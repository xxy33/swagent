"""
固废领域专业术语库
提供术语查询、翻译、定义查找等功能
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class TerminologyDB:
    """专业术语数据库"""

    def __init__(self, data_path: Optional[Path] = None):
        """
        初始化术语库

        Args:
            data_path: 数据文件路径，默认为模块内置路径
        """
        if data_path is None:
            data_path = Path(__file__).parent / "data" / "terminology.json"

        self.data_path = Path(data_path)
        self._terminology = None
        self._load_data()

    def _load_data(self):
        """加载术语数据"""
        if self.data_path.exists():
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self._terminology = json.load(f)

    def get_term(self, term: str, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取术语信息

        Args:
            term: 术语（英文或缩写）
            category: 类别，如 'waste_management', 'technical_terms'

        Returns:
            术语信息字典
        """
        if not self._terminology:
            return None

        terminology = self._terminology.get('terminology', {})

        # 如果指定类别，只在该类别中查找
        if category:
            cat_data = terminology.get(category, {})
            return cat_data.get(term)

        # 否则在所有类别中查找
        for cat_data in terminology.values():
            if isinstance(cat_data, dict) and term in cat_data:
                return cat_data[term]

        return None

    def translate(self, term: str, to_language: str = 'zh') -> Optional[str]:
        """
        翻译术语

        Args:
            term: 术语（英文或中文）
            to_language: 目标语言 ('zh' 或 'en')

        Returns:
            翻译结果
        """
        if not self._terminology:
            return None

        terminology = self._terminology.get('terminology', {})

        # 遍历所有类别查找
        for cat_data in terminology.values():
            if not isinstance(cat_data, dict):
                continue

            for term_key, term_data in cat_data.items():
                if not isinstance(term_data, dict):
                    continue

                # 检查是否匹配
                if term_key.lower() == term.lower():
                    if to_language == 'zh':
                        return term_data.get('term_zh') or term_data.get('full_name_zh')
                    else:
                        return term_data.get('term_en') or term_data.get('full_name_en') or term_key

                # 反向匹配（中文到英文）
                if to_language == 'en':
                    term_zh = term_data.get('term_zh') or term_data.get('full_name_zh')
                    if term_zh == term:
                        return term_data.get('term_en') or term_data.get('full_name_en') or term_key

        return None

    def get_definition(self, term: str) -> Optional[str]:
        """
        获取术语定义

        Args:
            term: 术语

        Returns:
            定义文本
        """
        term_data = self.get_term(term)

        if term_data:
            return term_data.get('definition')

        return None

    def get_abbreviation(self, full_name: str) -> Optional[str]:
        """
        获取缩写

        Args:
            full_name: 全称（英文或中文）

        Returns:
            缩写
        """
        if not self._terminology:
            return None

        terminology = self._terminology.get('terminology', {})

        for cat_data in terminology.values():
            if not isinstance(cat_data, dict):
                continue

            for abbr, term_data in cat_data.items():
                if not isinstance(term_data, dict):
                    continue

                # 检查全称匹配
                full_en = term_data.get('full_name_en', '')
                full_zh = term_data.get('full_name_zh', '')

                if full_name.lower() == full_en.lower() or full_name == full_zh:
                    return abbr

        return None

    def expand_abbreviation(self, abbr: str, language: str = 'zh') -> Optional[str]:
        """
        展开缩写为全称

        Args:
            abbr: 缩写
            language: 语言 ('zh' 或 'en')

        Returns:
            全称
        """
        term_data = self.get_term(abbr)

        if term_data:
            if language == 'zh':
                return term_data.get('full_name_zh')
            else:
                return term_data.get('full_name_en')

        return None

    def search_terms(self, keyword: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索术语

        Args:
            keyword: 搜索关键词
            category: 限定类别

        Returns:
            匹配的术语列表
        """
        if not self._terminology:
            return []

        results = []
        terminology = self._terminology.get('terminology', {})
        keyword_lower = keyword.lower()

        # 确定搜索范围
        if category:
            search_dict = {category: terminology.get(category, {})}
        else:
            search_dict = terminology

        # 搜索
        for cat_name, cat_data in search_dict.items():
            if not isinstance(cat_data, dict):
                continue

            for term_key, term_data in cat_data.items():
                if not isinstance(term_data, dict):
                    continue

                # 检查匹配
                if self._match_term(term_key, term_data, keyword_lower):
                    results.append({
                        'term': term_key,
                        'category': cat_name,
                        'data': term_data
                    })

        return results

    def _match_term(self, term_key: str, term_data: Dict[str, Any], keyword: str) -> bool:
        """
        检查术语是否匹配关键词

        Args:
            term_key: 术语键
            term_data: 术语数据
            keyword: 关键词（小写）

        Returns:
            是否匹配
        """
        # 检查术语键
        if keyword in term_key.lower():
            return True

        # 检查中英文名称
        searchable_fields = [
            'term_zh', 'term_en', 'full_name_zh', 'full_name_en', 'definition'
        ]

        for field in searchable_fields:
            value = term_data.get(field, '')
            if isinstance(value, str) and keyword in value.lower():
                return True

        # 检查别名
        aliases = term_data.get('aliases', [])
        if isinstance(aliases, list):
            for alias in aliases:
                if keyword in alias.lower():
                    return True

        return False

    def get_related_terms(self, term: str) -> List[str]:
        """
        获取相关术语

        Args:
            term: 术语

        Returns:
            相关术语列表
        """
        term_data = self.get_term(term)

        if term_data and 'related_terms' in term_data:
            return term_data['related_terms']

        return []

    def get_terms_by_category(self, category: str) -> Dict[str, Any]:
        """
        获取某个类别的所有术语

        Args:
            category: 类别名称

        Returns:
            该类别的术语字典
        """
        if not self._terminology:
            return {}

        terminology = self._terminology.get('terminology', {})
        return terminology.get(category, {})

    def get_all_categories(self) -> List[str]:
        """
        获取所有类别

        Returns:
            类别列表
        """
        if not self._terminology:
            return []

        return self._terminology.get('categories', [])

    def get_waste_type_properties(self, waste_type: str) -> Optional[Dict[str, Any]]:
        """
        获取废物类型的属性

        Args:
            waste_type: 废物类型

        Returns:
            属性字典
        """
        waste_types = self.get_terms_by_category('waste_types')
        term_data = waste_types.get(waste_type)

        if term_data:
            return term_data.get('properties', {})

        return None

    def get_treatment_method_info(self, method: str) -> Optional[Dict[str, Any]]:
        """
        获取处理方法信息

        Args:
            method: 处理方法

        Returns:
            处理方法信息
        """
        methods = self.get_terms_by_category('treatment_methods')
        return methods.get(method)

    def explain_term(self, term: str, detailed: bool = True) -> str:
        """
        解释术语（生成人类可读的说明）

        Args:
            term: 术语
            detailed: 是否包含详细信息

        Returns:
            解释文本
        """
        term_data = self.get_term(term)

        if not term_data:
            return f"未找到术语 '{term}' 的信息"

        explanation = []

        # 基本信息
        term_zh = term_data.get('term_zh') or term_data.get('full_name_zh', '')
        term_en = term_data.get('term_en') or term_data.get('full_name_en', term)

        if term_zh:
            explanation.append(f"{term} ({term_zh})")
        else:
            explanation.append(term)

        # 定义
        definition = term_data.get('definition')
        if definition:
            explanation.append(f"定义: {definition}")

        if not detailed:
            return '\n'.join(explanation)

        # 详细信息
        if 'properties' in term_data:
            explanation.append(f"属性: {term_data['properties']}")

        if 'advantages' in term_data:
            explanation.append(f"优点: {', '.join(term_data['advantages'])}")

        if 'disadvantages' in term_data:
            explanation.append(f"缺点: {', '.join(term_data['disadvantages'])}")

        if 'related_terms' in term_data:
            explanation.append(f"相关术语: {', '.join(term_data['related_terms'])}")

        if 'aliases' in term_data:
            explanation.append(f"别名: {', '.join(term_data['aliases'])}")

        return '\n'.join(explanation)


# 全局单例
_global_terminology_db: Optional[TerminologyDB] = None


def get_terminology_db() -> TerminologyDB:
    """
    获取全局术语库实例

    Returns:
        TerminologyDB实例
    """
    global _global_terminology_db

    if _global_terminology_db is None:
        _global_terminology_db = TerminologyDB()

    return _global_terminology_db
